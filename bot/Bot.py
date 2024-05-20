import logging
import re
import paramiko
import psycopg2
from psycopg2 import Error
from tabulate import tabulate
import os
from dotenv import load_dotenv

from telegram import Update, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()
TOKEN = os.getenv('TOKEN')
hostname = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_username = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_database = os.getenv('DB_DATABASE')

# Подключаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
#    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Список возможных команд:\n'
                              '/findPhoneNumbers - Поиск номеров в данном вами тексте и возможность занести в таблицу\n'
                              '/findEmail - Поиск email-в в данном вами тексте и возможность занести в таблицу\n'
                              '/CheckPassword - Проверка вашего пароля на сложность\n'
                              '/handle_Command - Лист команд для снятия метроков с сервера\n'
                              '/get_emails - Вывод таблицы email-в\n'
                              '/get_phones - Вывод таблицы телефонов\n'
                              '/get_repl_logs - Вывод логов Базы данный(Ошибки, Репликация)\n')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'


def findPhoneNumbers(update: Update, context):
    user_input = update.message.text

    phoneNumRegex = re.compile(r"\+?7[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|\+?7[ -]?\d{10}|8[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|8[ -]?\d{10}")  # формат 8 (000) 000-00-00

    phoneNumberList = phoneNumRegex.findall(user_input)

    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены')
        return

    phoneNumbers = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i + 1}. {phoneNumberList[i]}\n'  # Записываем очередной номер

    update.message.reply_text(phoneNumbers)  # Отправляем сообщение пользователю
    update.message.reply_text("Хотите занести их в таблицу? Да/Нет")
    print(0)
    context.user_data['phone_numbers'] = phoneNumberList
    print(1)
    return 'RecordPhone'

def RecordPhone(update: Update, context):
    user2_input = update.message.text
    print(3)
    PhoneList = context.user_data['phone_numbers']
    print(4)
    if user2_input == 'Да':
        if save_to_database2(PhoneList):
            update.message.reply_text("Заносим данные в таблицу...")
            update.message.reply_text("Успешно!\n"
                                      "Можете проверить - /get_phones")
        else:
            update.message.reply_text("Ошибка при сохранении информации в базу данных.")
    else:
        update.message.reply_text("Ну и ладно, хорошего вам дня!")

    return ConversationHandler.END

def save_to_database2(Phones):
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(user=db_username,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=db_database)

        # Создание курсора для выполнения SQL-запросов
        cursor = connection.cursor()

        # Пример SQL-запроса для вставки данных в таблицу
        for Phone in Phones:
            # data = cursor.fetchall()
            cursor.execute("SELECT MAX(customerid) AS LastId FROM Phones;")
            id = cursor.fetchone()[0] + 1
            cursor.execute("INSERT INTO Phones (customerid, numberphone ) VALUES (%s, %s)", (id, Phone,))

        # Подтверждение изменений в базе данных
        connection.commit()

        # Закрытие курсора и соединения
        cursor.close()
        connection.close()

        return True  # Успешное сохранение

    except (Exception, psycopg2.Error) as error:
        print("Ошибка при работе с PostgreSQL:", error)
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        return False  # Ошибка при сохранении


def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска Email-в: ')

    return 'findEmail'

def findEmail(update: Update, context):
    user_input = update.message.text

    EmailRegex = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")

    EmailList = EmailRegex.findall(user_input)

    if not EmailList:
        update.message.reply_text('Email-ы не найдены')
        return

    Email = ''
    for i in range(len(EmailList)):
        Email += f'{i + 1}. {EmailList[i]}\n'
    update.message.reply_text(Email)
    update.message.reply_text("Хотите занести их в таблицу? Да/Нет")
    print(0)
    context.user_data['emails'] = EmailList
    print(1)
    return 'RecordEmail'
    # return ConversationHandler.END

def RecordEmail(update: Update, context):
    user2_input = update.message.text
    print(3)
    EmailList = context.user_data['emails']
    print(4)
    if user2_input == 'Да':
        if save_to_database(EmailList):
            update.message.reply_text("Заносим данные в таблицу...")
            update.message.reply_text("Успешно!\n"
                                      "Можете проверить - /get_emails")
        else:
            update.message.reply_text("Ошибка при сохранении информации в базу данных.")
    else:
        update.message.reply_text("Ну и ладно, хорошего вам дня!")

    return ConversationHandler.END

def save_to_database(Emails):
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(user=db_username,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=db_database)

        # Создание курсора для выполнения SQL-запросов
        cursor = connection.cursor()

        # Пример SQL-запроса для вставки данных в таблицу
        for email in Emails:
            # data = cursor.fetchall()
            cursor.execute("SELECT MAX(customerid) AS LastId FROM Emails;")
            id = cursor.fetchone()[0] + 1
            cursor.execute("INSERT INTO Emails (customerid, email) VALUES (%s, %s)", (id, email,))

        # Подтверждение изменений в базе данных
        connection.commit()

        # Закрытие курсора и соединения
        cursor.close()
        connection.close()

        return True  # Успешное сохранение

    except (Exception, psycopg2.Error) as error:
        print("Ошибка при работе с PostgreSQL:", error)
        return False  # Ошибка при сохранении


def PasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки его сложности: ')

    return 'CheckPassword'

def CheckPassword(update: Update, context):
    user_input = update.message.text
    PaswordRegex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$")

    if re.match(PaswordRegex, user_input):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')

    return ConversationHandler.END


def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def handleCommand(update: Update, context):

    update.message.reply_text('Введите команду для получения мериков с kali: \n'
                              '/get_release - О релизе. \n'
                              '/get_uname - Об архитектуры процессора, имени хоста системы и версии ядра.\n'
                              '/get_uptime - О времени работы.\n'
                              '/get_df - Сбор информации о состоянии файловой системы.\n'
                              '/get_free - Сбор информации о состоянии оперативной памяти.\n'
                              '/get_mpstat - Сбор информации о производительности системы.\n'
                              '/get_w - Сбор информации о работающих в данной системе пользователях.\n'
                              '/get_auths - Последние 10 входов в систему.\n'
                              '/get_criticalv - Последние 5 критических события.\n'
                              '/get_ps - Сбор информации о запущенных процессах.\n'
                              '/get_ss - Сбор информации об используемых портах.\n'
                              '/get_apt_list - Сбор информации об установленных пакетах.\n'
                              '/get_services - Сбор информации о запущенных сервисах.\n')

    return ConversationHandler.END

def ssh_connect(hostname, username, password):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=hostname, username=username, password=password)
        return ssh_client
    except Exception as e:
        print(f"Ошибка при подключении: {e}")
        return None

# Функция для выполнения команды на удаленном сервере
def execute_command(ssh_client, command):
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode()
        return output
    except Exception as e:
        print(f"Ошибка при выполнении команды: {e}")
        return None

def handle_command(update: Update, context):

    user_input = update.message.text
    hostname1 = hostname
    username1 = username
    password1 = password

    ssh_client = ssh_connect(hostname1, username1, password1)
    if ssh_client:
        if user_input == "get_release":
            return update.message.reply_text(execute_command(ssh_client, "lsb_release -a"))
        elif user_input == "get_uname":
            update.message.reply_text(execute_command(ssh_client, "uname -a"))
        elif user_input == "get_uptime":
            update.message.reply_text(execute_command(ssh_client, "uptime"))
        elif user_input == "get_df":
            update.message.reply_text(execute_command(ssh_client, "df -h"))
        elif user_input == "get_free":
            update.message.reply_text(execute_command(ssh_client, "free -h"))
        elif user_input == "get_mpstat":
            update.message.reply_text(execute_command(ssh_client, "mpstat"))
        elif user_input == "get_w":
            update.message.reply_text(execute_command(ssh_client, "w"))
        elif user_input == "get_auths":
            update.message.reply_text(execute_command(ssh_client, "last -n 10"))
        elif user_input == "get_critical":
            update.message.reply_text(execute_command(ssh_client, "tail -n 5 /var/log/syslog"))
        elif user_input == "get_ps":
            update.message.reply_text(execute_command(ssh_client, "ps aux"))
        elif user_input == "get_ss":
            update.message.reply_text(execute_command(ssh_client, "netstat -tuln"))
        elif user_input == "get_apt_list":
            update.message.reply_text(execute_command(ssh_client, "apt list --installed"))
        elif user_input == "get_services":
            update.message.reply_text(execute_command(ssh_client, "service --status-all"))
        else:
            update.message.reply_text("Неверная команда")
    else:
        update.message.reply_text("Ошибка при подключении к серверу")

    return ConversationHandler.END

def get_emailsCommand(update: Update, context):
    update.message.reply_text('База данных Email-ов: ')
    logging.basicConfig(
        filename='app.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
        encoding="utf-8"
    )

    connection = None

    try:
        connection = psycopg2.connect(user=db_username,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=db_database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Emails;")
        data = cursor.fetchall()
        columns = ["ID", "Emails:"]
        update.message.reply_text(tabulate(data, headers=columns))
        # for row in data:
        #     update.message.reply_text(row)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ConversationHandler.END

def get_phonesCommand(update: Update, context):
    update.message.reply_text('База данных номеров: ')
    logging.basicConfig(
        filename='app.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
        encoding="utf-8"
    )

    connection = None

    try:
        connection = psycopg2.connect(user=db_username,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=db_database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Phones;")
#	cursor.execute("SHOW TABLES;")
        data = cursor.fetchall()
        columns = ["ID","Phones:"]
        update.message.reply_text(tabulate(data, headers=columns))
        # for row in data:
        #     update.message.reply_text(tabulate(row))
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ConversationHandler.END
def get_release(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, "lsb_release -a"))
    return ConversationHandler.END

# Функция обработки команды /get_uname
def get_uname(update: Update, context)-> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'uname -a'))
    return ConversationHandler.END

# Функция обработки команды /get_uptime
def get_uptime(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'uptime'))
    return ConversationHandler.END

# Функция обработки команды /get_df
def get_df(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'df -h'))
    return ConversationHandler.END

# Функция обработки команды /get_free
def get_free(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'free -h'))
    return ConversationHandler.END

# Функция обработки команды /get_mpstat
def get_mpstat(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'mpstat'))
    return ConversationHandler.END

# Функция обработки команды /get_w
def get_w(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'w'))
    return ConversationHandler.END


# Функция обработки команды /get_auths
def get_auths(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'last -n 10'))
    return ConversationHandler.END

# Функция обработки команды /get_critical
def get_critical(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'tail -n 5 /var/log/syslog'))
    return ConversationHandler.END

# Функция обработки команды /get_ps
def get_ps(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'ps aux | head -n 10'))
    return ConversationHandler.END

# Функция обработки команды /get_ss
def get_ss(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'netstat -tuln'))
    return ConversationHandler.END

# Функция обработки команды /get_apt_list
def get_apt_list(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    if context.args:
        package_name = ' '.join(context.args)
        command = f"apt-cache show {package_name}"
    else:
        command = "dpkg --get-selections | head -n 5"
    update.message.reply_text(execute_command(ssh_client, command))
    return ConversationHandler.END

# Функция обработки команды /get_services
def get_services(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'service --status-all'))
    return ConversationHandler.END

#tail /var/log/postgresql/postgresql-15-main.log

def get_repl_logs(update: Update, context) -> None:
    ssh_client = ssh_connect(hostname, username, password)
    update.message.reply_text(execute_command(ssh_client, 'tail -30 /var/log/postgresql/postgresql-15-main.log'))
    return ConversationHandler.END
def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers1 = ConversationHandler(
        entry_points=[CommandHandler('findPhoneNumbers', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'RecordPhone': [MessageHandler(Filters.text & ~Filters.command, RecordPhone)],
        },
        fallbacks=[]
    )
    convHandlerFindPhoneNumbers2 = ConversationHandler(
        entry_points=[CommandHandler('findEmail', findEmailCommand)],
        states={
            'findEmail': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'RecordEmail': [MessageHandler(Filters.text & ~Filters.command, RecordEmail)],
        },
        fallbacks=[]
    )

    convHandlerFindPhoneNumbers3 = ConversationHandler(
        entry_points=[CommandHandler('CheckPassword', PasswordCommand)],
        states={
            'CheckPassword': [MessageHandler(Filters.text & ~Filters.command, CheckPassword)],
        },
        fallbacks=[]
    )

    convHandlerFindPhoneNumbers4 = ConversationHandler(
        entry_points=[CommandHandler('handle_command', handleCommand)],
        states={
            'handle_command': [MessageHandler(Filters.text & ~Filters.command, handleCommand)],
        },
        fallbacks=[]
    )

    convHandlerFindPhoneNumbers5 = ConversationHandler(
        entry_points=[CommandHandler('get_emails', get_emailsCommand)],
        states={
            'get_emails': [MessageHandler(Filters.text & ~Filters.command, get_emailsCommand)],
        },
        fallbacks=[]
    )

    convHandlerFindPhoneNumbers6 = ConversationHandler(
        entry_points=[CommandHandler('get_phones', get_phonesCommand)],
        states={
            'get_phones': [MessageHandler(Filters.text & ~Filters.command, get_phonesCommand)],
        },
        fallbacks=[]
    )

    # convHandlerFindPhoneNumbers7 = ConversationHandler(
    #     entry_points=[CommandHandler('RecordEmail', findEmail)],
    #     states={
    #         'RecordEmail': [MessageHandler(Filters.text & ~Filters.command, RecordEmail)],
    #     },
    #     fallbacks=[]
    # )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers1)
    dp.add_handler(convHandlerFindPhoneNumbers2)
    dp.add_handler(convHandlerFindPhoneNumbers3)
    dp.add_handler(convHandlerFindPhoneNumbers4)
    dp.add_handler(convHandlerFindPhoneNumbers5)
    dp.add_handler(convHandlerFindPhoneNumbers6)
    # dp.add_handler(convHandlerFindPhoneNumbers7)
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("RecordEmail", RecordEmail))
    # dp.add_handler(CommandHandler("echo2", echo2))
    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()

