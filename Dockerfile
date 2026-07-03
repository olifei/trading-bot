FROM python:3.12-slim
WORKDIR /app
COPY trading_assistant/requirements.txt /app/trading_assistant/requirements.txt
RUN pip install --no-cache-dir -r /app/trading_assistant/requirements.txt
COPY trading_assistant /app/trading_assistant
COPY trading_bot_server.py streamlit_frontend.py run.sh /app/
RUN chmod +x /app/run.sh
ENV PORT 8080
EXPOSE 8080
CMD ["/app/run.sh"]
