import csv
import datetime
import io
import re

from flask import Flask, render_template, request, send_file

app = Flask(__name__)


def translate(input_str):
    return input_str \
        .replace('€Ş', 'ę') \
        .replace('˝_', 'ź') \
        .replace('˝â', 'ł') \
        .replace('_¸', 'ó') \
        .replace('€ă', 'Ą') \
        .replace('˝ä', 'Ś') \
        .replace('€ ', 'Ć') \
        .replace('_Ň', 'Ó') \
        .replace('˝', 'Ł') \


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    input_file = request.files['file']
    content = input_file.read().decode('windows-1250', 'ignore')
    translated_content = translate(content)
    # print(translated_content)
    # return "OK"
    qif_content = qif_file(io.StringIO(translated_content))

    # Creating the byteIO object from the StringIO Object
    mem = io.BytesIO()
    mem.write(qif_content.encode('utf-8'))
    # seeking was necessary. Python 3.5.2, Flask 0.12.2
    mem.seek(0)

    return send_file(
        mem,
        as_attachment=True,
        download_name=input_file.filename + '.qif',
        mimetype='text/plain'
    )


class pekao(csv.Dialect):
    """Describe the usual properties of PEKAO-generated CSV files."""
    delimiter = ';'
    quoting = csv.QUOTE_NONE
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL


csv.register_dialect("pekao", pekao)


def read_pekao_csv_transactions(input_stream):
    operations = []
    reader = csv.DictReader(input_stream, dialect="pekao")
    print(reader.fieldnames)
    for row in reader:
        operation = {
            'date': datetime.datetime.strptime(row['Data księgowania'], '%d.%m.%Y'),
            'description': re.sub(' +', ' ', row['Typ operacji'] + ' ' + row['Nadawca / Odbiorca'] + ' ' + row['Tytułem']),
            'amount': "{:.2f}".format(float(row['Kwota operacji'].replace(' ', '').replace(',', '.'))).replace('.', ',')
        }
        operations.append(operation)
    return operations


def qif_header(acount_name):
    return "!Account\nN{}\nTBank\n^\n!Type:Bank\n".format(acount_name)


def qif_transaction(operation):
    return "D{}\nP{}\nT{}\n^\n".format(operation['date'].strftime('%Y-%m-%d'), operation['description'],
                                       operation['amount'])


def qif_file(input_stream):
    operations = read_pekao_csv_transactions(input_stream)
    qif = qif_header('Pekao-net') + ''.join(list(map(qif_transaction, operations)))
    return qif


if __name__ == '__main__':
    app.run(debug=True)






