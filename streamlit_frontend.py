import streamlit as st
import plotly.express as px
import pandas as pd
import json
import socket
import logging

from trading_assistant.services.database.firestore_client import get_firestore_client
from trading_assistant.services.compliance.kyc_api import get_kyc_status
from trading_assistant.services.compliance.region_api import get_user_info, get_region_restrictions

logger = logging.getLogger("streamlit_frontend")
logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="Crypto Portfolio Manager",
    page_icon="💹",
    layout="wide"
)

if "user_id" not in st.session_state:
    st.session_state.user_id = "user1"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

SERVER_ADDRESS = './trading_bot_socket'
MAX_BUFFER_SIZE = 65536

def query_trading_assistant_server(user_id, message):
    request_data = {"user_id": user_id, "message": message}
    try:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SERVER_ADDRESS)
        client_socket.sendall(json.dumps(request_data).encode())
        response_data = client_socket.recv(MAX_BUFFER_SIZE)
        client_socket.close()
        if response_data:
            try:
                return json.loads(response_data.decode())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse server response: {e} - Response: {response_data.decode()[:200]}")
                return [{"author": "error", "text": f"Failed to parse server response: {response_data.decode()[:100]}..."}]
        else:
            logger.error("Server returned no data")
            return [{"author": "error", "text": "Server returned no data"}]
    except socket.error as e:
        logger.error(f"Socket connection error: {e}")
        return [{"author": "error", "text": f"Cannot connect to trading assistant server: {e}"}]
    except Exception as e:
        logger.error(f"Unknown error during server communication: {e}")
        return [{"author": "error", "text": f"Unknown error during server communication: {str(e)}"}]

def display_portfolio(user_id):
    try:
        db = get_firestore_client()
        portfolio_doc = db.collection("portfolios").document(user_id).get()
        if not portfolio_doc.exists:
            st.error(f"Portfolio data not found for user {user_id}")
            return
        portfolio = portfolio_doc.to_dict()
        total_value = float(portfolio.get('total_balance_usdt', 0))
        st.markdown(f"<h3 style='text-align: center;'>Total Assets: ${total_value:,.2f}</h3>", unsafe_allow_html=True)

        if 'assets' in portfolio and portfolio['assets']:
            assets = portfolio['assets']
            min_display_threshold = 0.000001
            filtered_assets_data = [
                {"Coin": symbol, "Quantity": float(details.get('total', 0)), "Value (USD)": float(details.get('value_usdt', 0))}
                for symbol, details in assets.items() if float(details.get('total', 0)) >= min_display_threshold
            ]
            if not filtered_assets_data:
                st.info("No assets to display (all asset quantities are zero).")
                return

            df_display = pd.DataFrame(filtered_assets_data)
            
            st.caption("Asset Distribution")
            if not df_display.empty and df_display["Value (USD)"].sum() > 0:
                fig = px.pie(df_display, values="Value (USD)", names="Coin", hole=0.4, color_discrete_sequence=px.colors.qualitative.Plotly)
                fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=250, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to generate chart.")
            
            st.markdown("---")
            st.caption("Asset Details")
            detail_df_data = [
                {"Coin": item["Coin"], "Quantity": item["Quantity"], 
                 "Price (USD)": (item["Value (USD)"] / item["Quantity"]) if item["Quantity"] > 0 else 0, 
                 "Value (USD)": item["Value (USD)"]}
                for item in filtered_assets_data
            ]
            detail_df_display = pd.DataFrame(detail_df_data)
            if not detail_df_display.empty:
                for col_name in ["Price (USD)", "Value (USD)"]:
                    if col_name in detail_df_display.columns:
                        detail_df_display[col_name] = detail_df_display[col_name].map("${:,.2f}".format)
                table_height = min(250, (len(detail_df_display) + 1) * 35 + 3) 
                st.dataframe(detail_df_display, use_container_width=True, hide_index=True, height=table_height)
            else:
                st.info("No asset details to display.")
        else:
            st.info("No asset data.")
    except Exception as e:
        st.error(f"Error loading portfolio: {str(e)}")

def display_user_profile(user_id_to_display):
    try:
        kyc_info = get_kyc_status(user_id_to_display)
        user_details = get_user_info(user_id_to_display)
        region = user_details.get("region", "UNKNOWN")
        restrictions = get_region_restrictions(region)

        st.sidebar.markdown(f"**User ID:** {user_id_to_display}")
        st.sidebar.markdown(f"**Region:** {region}")
        
        kyc_verified_status = "Yes" if kyc_info.get("kyc_verified", False) else "No"
        st.sidebar.markdown(f"**KYC Verified:** {kyc_verified_status}")
        
        st.sidebar.markdown(f"**Language:** {user_details.get('language', 'english').capitalize()}")
        
        restricted_coins = restrictions.get("restricted_coins", [])
        if restricted_coins:
            st.sidebar.markdown(f"**Restricted Coins:** {', '.join(restricted_coins)}")
        else:
            st.sidebar.markdown("**Restricted Coins:** None")
            
        restricted_trade_types = restrictions.get("restricted_trade_types", [])
        if restricted_trade_types:
            st.sidebar.markdown(f"**Restricted Trade Types:** {', '.join(restricted_trade_types)}")
        else:
            st.sidebar.markdown("**Restricted Trade Types:** None")
            
        max_amount = restrictions.get("max_transaction_amount", 0)
        st.sidebar.markdown(f"**Max Transaction Amount (USDT):** {max_amount:,.2f}")

    except Exception as e:
        st.sidebar.error(f"Error loading user profile: {str(e)}")

def chat_interface(user_id):
    chat_display_area = st.container(height=700)
    with chat_display_area:
        if not st.session_state.chat_history:
            st.session_state.chat_history.append({"author": "trading_assistant", "text": f"Hello, {st.session_state.user_id}! I am your Trading Assistant. How can I help you?"})
        for msg in st.session_state.chat_history:
            with st.chat_message(name="user" if msg["author"] == "user" else "assistant"):
                if msg["author"] == "error": st.error(msg["text"])
                else: st.markdown(msg["text"])

    if st.session_state.get("pending_input"):
        input_to_process = st.session_state.pending_input
        st.session_state.pending_input = None

        with st.spinner("Assistant is thinking..."):
            try:
                responses = query_trading_assistant_server(user_id, input_to_process)
                
                if responses:
                    final_assistant_message = None
                    trade_result_message = None

                    for r in reversed(responses):
                        if not isinstance(r, dict):
                            logger.warning(f"Received non-dict response item: {r}")
                            st.session_state.chat_history.append({"author": "error", "text": f"Received incorrectly formatted response: {str(r)[:100]}"})
                            continue
                        
                        text_content = r.get("text", "")
                        author = r.get("author", "unknown")

                        if "Trade successful!" in text_content or "Trade ID" in text_content or "Trade failed" in text_content:
                            trade_result_message = r
                            break 
                        if author == "trading_assistant" and not final_assistant_message:
                            final_assistant_message = r

                    if trade_result_message:
                        st.session_state.chat_history.append(trade_result_message)
                        with st.expander("Trade Execution Result", expanded=True):
                            if "Trade successful!" in trade_result_message.get("text", ""): st.success("✅ Trade successful!")
                            elif "Trade failed" in trade_result_message.get("text", ""): st.error("❌ Trade failed!")
                            st.markdown(trade_result_message.get("text", ""))
                    elif final_assistant_message:
                        st.session_state.chat_history.append(final_assistant_message)
                    elif responses:
                        last_valid = next((r for r in reversed(responses) if isinstance(r, dict) and r.get("author") != "error"), None)
                        if last_valid: st.session_state.chat_history.append(last_valid)
                        elif responses[0].get("author") == "error" : st.session_state.chat_history.append(responses[0])
                else:
                    st.session_state.chat_history.append({"author": "error", "text": "No response from assistant, please try again later"})
            except Exception as e:
                st.session_state.chat_history.append({"author": "error", "text": f"Unexpected error processing user input: {str(e)}"})
            finally:
                st.rerun()

    user_input_val = st.chat_input("Enter your question or command...", key="chat_input_main")

    if user_input_val:
        st.session_state.chat_history.append({"author": "user", "text": user_input_val})
        st.session_state.pending_input = user_input_val 
        st.rerun()

def main():
    with st.sidebar:
        st.title("Crypto Portfolio Manager")
        try:
            db = get_firestore_client()
            portfolios_ref = db.collection("portfolios")
            user_docs = portfolios_ref.stream()
            user_ids = [doc.id for doc in user_docs]
            if not user_ids:
                st.sidebar.warning("No user data found, will use default user 'user1'")
                user_ids.append('user1')
                if 'user_id' not in st.session_state or st.session_state.user_id not in user_ids:
                    st.session_state.user_id = user_ids[0]
            
            selected_user = st.sidebar.selectbox(
                "Select User ID",
                options=user_ids,
                index=user_ids.index(st.session_state.user_id) if st.session_state.user_id in user_ids else 0,
                key="user_selector_sidebar"
            )
            if selected_user != st.session_state.user_id:
                st.session_state.user_id = selected_user
                st.session_state.chat_history = []
                st.rerun()
            st.sidebar.subheader(f"User Profile: {selected_user}")
            user_id = selected_user
            display_user_profile(user_id)
        except Exception as e:
            st.sidebar.error(f"Error loading user list or profile details: {str(e)}")
            user_id = st.session_state.user_id

    if user_id:
        main_area_col1, main_area_col2 = st.columns([2, 3])
        with main_area_col1:
            with st.expander("Portfolio Overview (Click to expand/collapse)", expanded=True):
                display_portfolio(user_id)
        with main_area_col2:
            chat_interface(user_id)
    else:
        st.error("Cannot determine user. Please refresh or check the sidebar.")

if __name__ == "__main__":
    main()
