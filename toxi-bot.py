
# This code is used to process audio files from the telegram bot, get the text from the audio file and generate an automated response.
# Este código se usa para procesar archivos de audio del bot de telegram, obtener el texto del archivo de audio y generar una respuesta automatizada.

# import the necessary libraries // importar las librerías necesarias
import os # operating system library that allows us to access the computer's file system // librería del sistema operativo que nos permite acceder al sistema de archivos del computador
import openai # library used to access the OpenAI API // librería usada para acceder a la API de OpenAI
import config # import the config file // importar el archivo de configuración
import org_data # import the org_data file // importar el archivo org_data
import csv # library used to read and write csv files // librería usada para leer y escribir archivos csv
import pandas as pd # library used to read and write csv files // librería usada para leer y escribir archivos csv
import logging # library used to log errors // librería usada para registrar errores
from requests import * # library used to make HTTP requests // librería usada para realizar solicitudes HTTP
from telegram import __version__ as TG_VER # import the telegram version // importar la versión de telegram
# Import the necessary classes from the telegram.ext library // Importar las clases necesarias de la biblioteca telegram.ext
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler

# set the OpenAI API key, so the code can access the API // establecer la clave de la API de OpenAI, para que el código pueda acceder a la API
openai.api_key = config.openai_api_key

# set the logging level // establecer el nivel de registro
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# create the logger // crear el registrador
logger = logging.getLogger(__name__)

# decoding means converting the bytes (0s and 1s) into a string // la decodificación significa convertir los bytes (0s y 1s) en una cadena de texto
def decode_utf8(text: bytes) -> str: 
    # Encode the string with UTF-8 // Codificar la cadena con UTF-8
    encoded_text = text.encode('utf-8')
    # Decode the bytes with UTF-8 // Decodificar los bytes con UTF-8
    decoded_text = encoded_text.decode('utf-8')
    return decoded_text

# use ffmpeg to convert the audio file to a wav file // usar ffmpeg para convertir el archivo de audio a un archivo wav
def convert_to_wav(audio_file):
    # get the name of the audio file // obtener el nombre del archivo de audio
    audio_file_name = os.path.basename(audio_file)
    # get the name of the audio file without the extension // obtener el nombre del archivo de audio sin la extensión
    audio_file_name_without_extension = os.path.splitext(audio_file_name)[0]
    # create a new file name for the wav file // crear un nuevo nombre de archivo para el archivo wav
    new_file_name = audio_file_name_without_extension + ".wav"
    # use ffmpeg to convert the audio file to a wav file // usar ffmpeg para convertir el archivo de audio a un archivo wav
    os.system("ffmpeg -y -i "+audio_file+" "+new_file_name)
    # return the new file name // devolver el nuevo nombre de archivo
    return new_file_name

# main function that handles the audio files // función principal que maneja los archivos de audio
def handle_audio(update, context):
    # Extract the audio file from the message // Extraer el archivo de audio del mensaje
    audio_file = update.message.audio
    # reply to the message, telling the user the audio file was received // responder al mensaje, diciendo al usuario que se recibió el archivo de audio
    update.message.reply_text('Audio recibido. Esperá un toque que lo proceso. Te voy avisando.') 
    # download the audio file // descargar el archivo de audio
    file_path = audio_file.get_file().download()
    # convert the audio file to a wav file // convertir el archivo de audio a un archivo wav
    wav_audio = open(convert_to_wav(file_path),"rb")
    # call the OpenAI API to get the text from the audio file // llamar a la API de OpenAI para obtener el texto del archivo de audio
    transcription_object = openai.Audio.transcribe("whisper-1", wav_audio,language="es",prompt="esto es una nota de voz. hay momentos de silencio en el audio, cuidado con eso.")
    # print the text extracted from the audio file // imprimir el texto extraído del archivo de audio
    print("Transcription:\n"+transcription_object["text"])
    # reply with the text extracted from the audio file // responder con el texto extraído del archivo de audio
    update.message.reply_text(transcription_object["text"]) 
    
    # call the OpenAI API to generate a summary of the voice note // llamar a la API de OpenAI para generar un resumen de la nota de voz
    summary_gpt_response = openai.Completion.create(
        model="text-davinci-003",
        # The prompt is the text that the model will use to generate a response. I add some things about me so that the model can generate a more personalized response // El prompt es el texto que el modelo usará para generar una respuesta. Agrego algunas cosas sobre mí para que el modelo pueda generar una respuesta más personalizada
        prompt="Me acaban de enviar una nota de voz que dice lo siguiente: \n"+transcription_object["text"] + "\n --- FIN DE LA NOTA DE VOZ --- \n Crear, en español, un resumen breve de la nota de voz.",
        # The temperature is a number between 0 and 1 that determines how random the model's response will be // La temperatura es un número entre 0 y 1 que determina qué tan aleatoria será la respuesta del modelo
        temperature=0.7,
        # Tokens is kinda like the number of words the model will use to generate a response // Tokens es como el número de palabras que el modelo usará para generar una respuesta
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    # get the text from the response // obtener el texto de la respuesta
    summary_text = (summary_gpt_response.choices[0].text)
    # decode the text // decodificar el texto
    decoded_summary_text = decode_utf8(summary_text)
    # print the decoded text // imprimir el texto decodificado
    print("Summary:\n"+decoded_summary_text)
    # Send the summary to the user // Enviar el resumen al usuario
    update.message.reply_text(decoded_summary_text)
    # call the OpenAI API to generate a reply to the voice note // llamar a la API de OpenAI para generar una respuesta a la nota de voz
    reply_gpt_response = openai.Completion.create(
        model="text-davinci-003",
        prompt="Me acaban de enviar una nota de voz que dice lo siguiente: \n"+transcription_object["text"] + "\n --- FIN DE LA NOTA DE VOZ --- \n Crear una respuesta de mi parte, "+config.my_name + "\n\n Sobre mí: \n" + config.about_me_spanish,
        temperature=0.7,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    # get the text from the response // obtener el texto de la respuesta
    reply_text = (reply_gpt_response.choices[0].text)
    # decode the text // decodificar el texto
    decoded_reply_text = decode_utf8(reply_text)
    # print the decoded text // imprimir el texto decodificado
    print("Reply:\n"+decoded_reply_text)
    # Send the reply to the user // Enviar la respuesta al usuario
    update.message.reply_text('Posible respuesta:')
    update.message.reply_text(decoded_reply_text)
    # delete the audio file // eliminar el archivo de audio
    os.remove(file_path)
    #delete the wav file // eliminar el archivo wav
    os.remove(wav_audio.name)

# when someone sends text to the bot, the message is added to messages.csv, including date and sender // cuando alguien envía texto al bot, el mensaje se agrega a messages.csv, incluyendo fecha y remitente
def handle_text(update, context):
    if "Whatsapp" in update.message.text:
        update.message.reply_text("Pegá mensajes de Whatsapp y lo voy a procesar. ¡Máximo 600 caracteres!")
        return
    if "Audios" in update.message.text:
        update.message.reply_text("Mandame audios y lo voy a procesar. ¡Máximo 60 segundos!")
        return
    # get the text from the message // obtener el texto del mensaje
    text = update.message.text
    # get the date from the message // obtener la fecha del mensaje
    date = update.message.date
    # get the sender from the message // obtener el remitente del mensaje
    sender = update.message.from_user.username
    

    # add the message to the csv file encoded in UTF-8 // agregar el mensaje al archivo csv codificado en UTF-8
    with open('messages.csv', 'a', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([date, sender, text,])
    
async def start(update, context):
    # creates a keyboard of buttons // crea un teclado de botones
    keyboard = [
        [
            InlineKeyboardButton("Whatsapp",callback_data="Whatsapp"), 
            InlineKeyboardButton("Audios",callback_data="Audios")
        ]
    ]
    # creates the keyboard markup // crea el markup del teclado
    reply_markup = InlineKeyboardMarkup(keyboard)

    # sends the message with the keyboard markup // envía el mensaje con el markup del teclado
    await update.message.reply_text("Querés que procese mensajes de Whatsapp o audios?", reply_markup=reply_markup)

async def button(update, context):

    # get the callback data // obtener los datos de devolución de llamada
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    # send a message when the command /help is issued // enviar un mensaje cuando se emite el comando /help
    await update.message.reply_text("Enviá /start para comenzar a usar el bot.")

def main() -> None:

    # Create the Updater and pass it your bot's token. // Crear el actualizador y pasarle el token de su bot.
    application = Application.builder().token(config.telegram_api_key).build()

    # set the handler for the /start command // establecer el manejador para el comando /start
    application.add_handler(CommandHandler("start", start))

    # set the handler for the buttons // establecer el manejador para los botones
    application.add_handler(CallbackQueryHandler(button))
    
    # set the handler for the /help command // establecer el manejador para el comando /help
    application.add_handler(CommandHandler("help", help_command))

    # start the bot // iniciar el bot
    application.run_polling()


if __name__ == '__main__':
    main()

