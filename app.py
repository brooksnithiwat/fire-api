from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from PIL import Image
import torch
import torchvision.transforms as transforms
from torchvision import models
import requests

app = Flask(__name__)

# LINE Channel Access Token and Channel Secret
CHANNEL_ACCESS_TOKEN = '1ine+u7yYPhDeluLPwdoJodgIPwtRJT0X5p1anOojeNXRRAGASWj8yRlQpoNEhUKBYLdZ2jp3Y98Ml+tgyChRkeNnZXk1zEhS3G/lESrzjBykq4gntfOmIwmfb0HsB/OvIJHIVqWf31gv9GkRAmYGgdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = '80411e32f8dfad6001544420d161ad5a'
USER_ID = 'U38c098d55f45ebc2f2498448a4a62d84'  # Replace with your LINE User ID

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Load trained model
model = models.resnet18(pretrained=False)
model.fc = torch.nn.Linear(model.fc.in_features, 3)  # 3 classes: "ไฟรุนแรง", "ไฟไหม้", "สถานการณ์ปกติ"
model.load_state_dict(torch.load("model.pth"))
model.eval()

def predict_image(filepath):
    # Load and resize the image
    image = Image.open(filepath)
    image = image.resize((224, 224))

    # Convert image to tensor and normalize
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    image = transform(image).unsqueeze(0)  # Add batch dimension

    # Predict the image category
    with torch.no_grad():
        output = model(image)
        _, predicted = torch.max(output, 1)
        return predicted.item()

@app.route("/webhook", methods=['POST'])
def webhook():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Get user ID from the event
    user_id = event.source.user_id
    print(f'User ID: {user_id}')

    # Reply to the user
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text=f'Your user ID is {user_id}')
    )

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    image_path = data['image_path']
    result = predict_image(image_path)

    if result == 0:
        message = "ไฟไหม้รุนแรง"
        img_path = "image/ไฟไหม้รุนแรง/fire.15.png"
        line_bot_api.push_message(USER_ID, TextMessage(text=message))
    elif result == 1:
        message = "ไฟไหม้"
        img_path = "image/ไฟไหม้/fire.1.png"
    elif result == 2:
        message = "สถานการณ์ปกติ"
        img_path = "image/ไม่ไฟไหม้/non_fire.1.png"
    else:
        message = "ไม่สามารถตรวจสอบได้"

    return {'message': message}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)

