### TODO: this is not bob2, either user bob2 or change name to our protocol name

# Function to create a BOB2 formatted message
def create_bob2_message(msg_type, payload):
    msg_type = msg_type.ljust(5)[:5]  # Ensure msg_type is exactly 5 characters
    msg_len = str(len(payload)).zfill(5)  # Ensure msg_len is exactly 5 characters
    return f"{msg_type}{msg_len}{payload}"

# Function to parse BOB2 messages
def parse_bob2_message(data):
    if len(data) < 10:
        return None, None
    msg_type = data[:5].strip()
    msg_len = int(data[5:10].strip())
    payload = data[10:10+msg_len]
    return msg_type, payload
