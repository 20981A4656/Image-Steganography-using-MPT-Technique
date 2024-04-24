from flask import Flask, render_template, request, redirect, send_file, flash
from werkzeug.utils import secure_filename
from PIL import Image
import os

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png'}

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def encode_image(img, message):
    encoded_img = img.copy()
    message += "###"  # End-of-message indicator
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    index = 0

    for x in range(img.size[0]):
        for y in range(img.size[1]):
            pixel = list(img.getpixel((x, y)))
            for n in range(3):  # Only modify the first three values (RGB)
                if index < len(binary_message):
                    pixel[n] = (pixel[n] & ~1) | int(binary_message[index])
                    index += 1
                else:
                    encoded_img.putpixel((x, y), tuple(pixel))
                    return encoded_img
            encoded_img.putpixel((x, y), tuple(pixel))
    return encoded_img

def decode_image(img):
    binary_data = ""
    message = ""
    
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            pixel = img.getpixel((x, y))
            for n in range(3):
                binary_data += str(pixel[n] & 1)
                if len(binary_data) == 8:
                    character = chr(int(binary_data, 2))
                    binary_data = ""
                    if message.endswith("###"):  # Check for end-of-message indicator
                        return message[:-3]  # Return message without the indicator
                    message += character
    return message[:-3] if message.endswith("###") else message  # Fallback if loop completes

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/encode', methods=['GET', 'POST'])
def encode():
    if request.method == 'POST':
        # Processing form data and file upload
        file = request.files.get('file')
        message = request.form.get('message')
        if not file or not message:
            flash('Missing file or message')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            img = Image.open(file.stream)
            encoded_img = encode_image(img, message)
            encoded_img_path = os.path.join(app.config['UPLOAD_FOLDER'], f"encoded_{filename}")
            encoded_img.save(encoded_img_path)
            return send_file(encoded_img_path, as_attachment=True)
    return render_template('encode.html')

@app.route('/decode', methods=['GET', 'POST'])
def decode():
    if request.method == 'POST':
        print("POST request received.")
        file = request.files.get('file')
        if not file:
            flash('Missing file')
            print("No file found in the request.")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            print(f"Processing file: {file.filename}")
            img = Image.open(file.stream)
            decoded_message = decode_image(img)
            print(f"Decoded message: {decoded_message}")
            return render_template('decoded.html', message=decoded_message)
        else:
            print("File provided is not allowed.")
    return render_template('decode.html')


if __name__ == '__main__':
    app.run(debug=True)
