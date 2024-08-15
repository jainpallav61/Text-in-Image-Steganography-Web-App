from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from PIL import Image
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

gkey = ""
tree = None

class Node:
    def __init__(self, prob, symbol, left=None, right=None):
        self.prob = prob
        self.symbol = symbol
        self.left = left
        self.right = right
        self.code = ''

codes = dict()

def Calculate_Codes(node, val=''):
    newVal = val + str(node.code)
    if(node.left):
        Calculate_Codes(node.left, newVal)
    if(node.right):
        Calculate_Codes(node.right, newVal)
    if(not node.left and not node.right):
        codes[node.symbol] = newVal
    return codes        

def Calculate_Probability(data):
    symbols = dict()
    for element in data:
        if symbols.get(element) is None:
            symbols[element] = 1
        else: 
            symbols[element] += 1     
    return symbols

def Output_Encoded(data, coding):
    encoding_output = []
    for c in data:
        encoding_output.append(coding[c])
    return ''.join(encoding_output)
        
def Huffman_Encoding(data):
    symbol_with_probs = Calculate_Probability(data)
    symbols = symbol_with_probs.keys()
    probabilities = symbol_with_probs.values()
    
    nodes = []   
    for symbol in symbols:
        nodes.append(Node(symbol_with_probs.get(symbol), symbol))
    
    while len(nodes) > 1:
        nodes = sorted(nodes, key=lambda x: x.prob)
        right = nodes[0]
        left = nodes[1]
        left.code = 0
        right.code = 1
        newNode = Node(left.prob + right.prob, left.symbol + right.symbol, left, right)
        nodes.remove(left)
        nodes.remove(right)
        nodes.append(newNode)
            
    huffman_encoding = Calculate_Codes(nodes[0])
    encoded_output = Output_Encoded(data, huffman_encoding)
    return encoded_output, nodes[0]  
    
def Huffman_Decoding(encoded_data, huffman_tree):
    tree_head = huffman_tree
    decoded_output = []
    for x in encoded_data:
        if x == '1':
            huffman_tree = huffman_tree.right   
        elif x == '0':
            huffman_tree = huffman_tree.left
        try:
            if huffman_tree.left.symbol is None and huffman_tree.right.symbol is None:
                pass
        except AttributeError:
            decoded_output.append(huffman_tree.symbol)
            huffman_tree = tree_head
        
    return ''.join(decoded_output)

def genData(data):
    newd = []
    for i in data:
        newd.append(format(ord(i), '08b'))
    return newd

def modPix(pix, data):
    datalist = genData(data)
    lendata = len(datalist)
    imdata = iter(pix)
    
    for i in range(lendata):
        pix = [value for value in imdata.__next__()[:3] +
               imdata.__next__()[:3] +
               imdata.__next__()[:3]]
        
        for j in range(0, 8):
            if (datalist[i][j] == '0') and (pix[j] % 2 != 0):
                pix[j] -= 1
            elif (datalist[i][j] == '1') and (pix[j] % 2 == 0):
                pix[j] -= 1

        if (i == lendata - 1):
            if (pix[-1] % 2 == 0):
                pix[-1] -= 1
        else:
            if (pix[-1] % 2 != 0):
                pix[-1] -= 1

        pix = tuple(pix)
        yield pix[0:3]
        yield pix[3:6]
        yield pix[6:9]

def encode_enc(newimg, data):
    w = newimg.size[0]
    (x, y) = (0, 0)

    for pixel in modPix(newimg.getdata(), data):
        newimg.putpixel((x, y), pixel)
        if (x == w - 1):
            x = 0
            y += 1
        else:
            x += 1

def decode(image):
    data = ''
    imgdata = iter(image.getdata())

    while (True):
        pixels = [value for value in imgdata.__next__()[:3] +
                  imgdata.__next__()[:3] +
                  imgdata.__next__()[:3]]
        binstr = ''
        for i in pixels[:8]:
            if i % 2 == 0:
                binstr += '0'
            else:
                binstr += '1'

        data += chr(int(binstr, 2))
        if pixels[-1] % 2 != 0:
            return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['GET', 'POST'])
def encode():
    if request.method == 'POST':
        file = request.files['image']
        message = request.form['message']
        key = request.form['key']

        if file and message and key:
            img = Image.open(file)
            global gkey, tree
            gkey = key
            encoded_message, tree = Huffman_Encoding(message)
            newimg = img.copy()
            encode_enc(newimg, encoded_message)
            
            img_io = BytesIO()
            newimg.save(img_io, 'PNG')
            img_io.seek(0)
            
            return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='encoded_image.png')
        else:
            flash("Please provide an image, message, and key.")
            return redirect(url_for('encode'))
    
    return render_template('encode.html')

@app.route('/decode', methods=['GET', 'POST'])
def decode_route():
    if request.method == 'POST':
        file = request.files['image']
        key = request.form['key']

        if file and key:
            img = Image.open(file)
            global gkey

            if gkey == key:
                hidden_data = decode(img)
                decoded_message = Huffman_Decoding(hidden_data, tree)
                return render_template('decode.html', message=decoded_message)
            else:
                flash("Incorrect key. Please try again.")
                return redirect(url_for('decode_route'))
    
    return render_template('decode.html')

if __name__ == '__main__':
    app.run(debug=True)
