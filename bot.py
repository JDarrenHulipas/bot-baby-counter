import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import init_db, registrar_evento, registrar_sueno_hora, obtener_resumen_diario, obtener_resumen_semanal
import datetime

# Reemplaza con el Token que te dio BotFather
TOKEN = "8977103597:AAHynXNMkUJi7dwRsXmhtBBvM1mvWuEHMB0"

# Configuración de logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Estoy listo para seguir el ritmo del bebé. Usa los comandos configurados para registrar el día a día."
    )

async def comando_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text.split()[0].lower()
    user_id = update.effective_user.id
    
    exito, contador = registrar_evento(user_id, comando)
    
    if not exito:
        limite = "4" if comando == "/biberon" else "2"
        await update.message.reply_text(f"⚠️ ¡Límite alcanzado! El comando {comando} ya se ha usado {limite} veces hoy.")
        return

    # Mensajes personalizados/alertas
    if comando == "/teta" and contador < 6:
        await update.message.reply_text(f"🍼 Teta registrada ({contador}/6 hoy). ¡Ánimo, faltan {6 - contador} para el mínimo recomendando!")
    else:
        await update.message.reply_text(f"✅ {comando.capitalize()} registrado con éxito. Total hoy: {contador}")

async def dormir_hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = " ".join(context.args)
    
    if not texto:
        await update.message.reply_text("Por favor, indica las horas. Ejemplo: `/DormirHora de 14:00 a 15:30`")
        return
        
    registrar_sueno_hora(user_id, texto)
    await update.message.reply_text(f"💤 Horario de sueño registrado: {texto}")

# Tareas programadas (Resúmenes)
async def enviar_resumen_diario(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    datos, sueno = obtener_resumen_diario()
    
    teta_count = datos.get('/teta', 0)
    teta_status = "✅ Mínimo alcanzado" if teta_count >= 6 else f"⚠️ Falta(n) {6 - teta_count} para el mínimo"

    resumen = (
        f"📊 **RESUMEN DIARIO DEL BEBÉ** 📊\n"
        f"----------------------------------------\n"
        f"🍼 Biberones: {datos.get('/biberon', 0)}/4\n"
        f"🤱 Teta: {teta_count} ({teta_status})\n"
        f"💩 Cacas: {datos.get('/caca', 0)}\n"
        f"💧 Pipís: {datos.get('/pipi', 0)}\n"
        f"🤸 Ejercicios: {datos.get('/ejercicios', 0)}/2\n"
        f"😴 Siestas (Rápidas): {datos.get('/dormir', 0)}\n"
    )
    
    if sueno:
        resumen += "\n🕒 **Horarios de sueño registrados:**\n"
        for s in sueno:
            resumen += f"- {s}\n"
            
    await context.bot.send_message(chat_id=chat_id, text=resumen, parse_mode="Markdown")

async def enviar_resumen_semanal(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    datos = obtener_resumen_semanal()
    
    resumen = (
        f"📈 **RESUMEN SEMANAL ACUMULADO** 📈\n"
        f"----------------------------------------\n"
        f"🍼 Biberones totales: {datos.get('/biberon', 0)}\n"
        f"🤱 Teta total: {datos.get('/teta', 0)}\n"
        f"💩 Cacas totales: {datos.get('/caca', 0)}\n"
        f"💧 Pipís totales: {datos.get('/pipi', 0)}\n"
        f"🤸 Ejercicios totales: {datos.get('/ejercicios', 0)}\n"
        f"😴 Sueños totales: {datos.get('/dormir', 0)}\n"
    )
    await context.bot.send_message(chat_id=chat_id, text=resumen, parse_mode="Markdown")

# Configurar alarmas de resúmenes automáticos al unirse al grupo
async def activar_alarmas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Eliminar jobs existentes para evitar duplicados
    current_jobs = context.job_queue.get_jobs_by_name(f"diario_{chat_id}")
    for job in current_jobs: job.schedule_removal()
    
    # Alarma diaria a las 23:59
    context.job_queue.run_daily(
        enviar_resumen_diario, 
        time=datetime.time(hour=23, minute=59, second=0), 
        chat_id=chat_id, 
        name=f"diario_{chat_id}"
    )
    
    # Alarma semanal (Domingos a las 23:59)
    context.job_queue.run_daily(
        enviar_resumen_semanal, 
        time=datetime.time(hour=23, minute=59, second=0), 
        days=(6,), # 6 es Domingo en la librería
        chat_id=chat_id, 
        name=f"semanal_{chat_id}"
    )
    
    await update.message.reply_text("⏰ Configurados resúmenes automáticos: Diario (23:59) y Semanal (Domingos 23:59).")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # Handlers de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activar_resumenes", activar_alarmas))
    app.add_handler(CommandHandler("dormirhora", dormir_hora))
    
    # Registrar resto de comandos que van a la BD
    for cmd in ['biberon', 'caca', 'pipi', 'ejercicios', 'teta', 'dormir']:
        app.add_handler(CommandHandler(cmd, comando_handler))

    print("Bot en marcha...")
    app.run_polling()

if __name__ == '__main__':
    main()