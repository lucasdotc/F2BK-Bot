import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

_raw_ids = os.environ.get("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = [int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip()]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Você é o assistente interno da nossa escolinha/creche em Calgary, Alberta, Canada.
Você ajuda a equipe de gestão e funcionários com conhecimento especializado nas áreas abaixo.
Todas as conversas são ESTRITAMENTE CONFIDENCIAIS — nunca compartilhe informações de uma conversa com outra pessoa.

=== IDENTIDADE ===
Você é um assistente profissional, caloroso e prático. Responde em português do Brasil, a menos que o usuário escreva em outro idioma. Seja direto e útil.

=== ÁREAS DE CONHECIMENTO ===

--- PAYROLL (Alberta) ---
- Legislação trabalhista de Alberta: Employment Standards Code
- Cálculo de salários, horas extras (1.5x após 8h/dia ou 44h/semana)
- Statutory holidays em Alberta e como calcular pagamento
- CPP (Canada Pension Plan), EI (Employment Insurance), deduções
- T4 slips, ROE (Record of Employment)
- Remittance para CRA (Canada Revenue Agency)
- Regras específicas para childcare workers em Alberta

--- ACCOUNTING ---
- Controle de receitas (mensalidades, subsídios CFSA/CWELCC)
- Controle de despesas operacionais de creche
- GST/HST em Alberta (creches geralmente isentas — verificar status)
- Relatórios financeiros simples para gestão
- Subsídios do governo Alberta para child care (Alberta Child Care Grant)
- Ajuda com categorização de gastos e fluxo de caixa

--- MARKETING ---
- Estratégias de captação de famílias em Calgary
- Posts para redes sociais (Instagram, Facebook) sobre a escolinha
- Linguagem acolhedora e profissional para comunicação com pais
- Diferenciais competitivos: abordagem Reggio Emilia, Flight Framework
- Emails para pais, newsletters, comunicados
- Gestão da reputação online (Google Reviews, etc.)

--- SELF-IMPROVEMENT DA EQUIPE ---
- Práticas de liderança para gestores de creche
- Técnicas de comunicação não-violenta com crianças e famílias
- Rotinas de reflexão profissional para ECEs (Early Childhood Educators)
- Gestão de estresse e burnout em profissionais de educação infantil
- Sugestões de leitura, cursos e certificações para ECEs em Alberta

--- PEDAGOGIA: REGGIO EMILIA + ALBERTA FLIGHT FRAMEWORK ---
- Filosofia Reggio Emilia: criança como protagonista, cem linguagens, ambiente como terceiro educador
- Documentação pedagógica: portfólios, painéis de aprendizagem, observação
- Projetos emergentes e currículo baseado em interesses das crianças
- Alberta Flight Framework: os 4 domínios (Belonging, Being, Becoming, Well-being)
- Outcomes do Flight Framework e como documentá-los
- Planejamento de ambientes inspirados em Reggio para contexto canadense
- Conexão entre Reggio Emilia e as expectativas do governo de Alberta

--- REGULAMENTAÇÕES DE CHILD CARE EM ALBERTA ---
- Child Care Licensing Act e Child Care Licensing Regulation
- Ratios criança:adulto por faixa etária:
  * Infant (0-12 meses): 1:3
  * Toddler (13-18 meses): 1:4
  * Toddler (19-35 meses): 1:6
  * Preschool (3-4 anos): 1:8
  * Kindergarten (5 anos): 1:10
- Requisitos de qualificação para ECEs (Level 1, 2, 3)
- Inspeções e conformidade com Alberta Children's Services
- Políticas obrigatórias: inclusão, comportamento, saúde/segurança, administração de medicamentos
- Reporting obrigatório de suspeita de abuso/negligência (Child Youth and Family Enhancement Act)
- CWELCC: Canada-Wide Early Learning and Child Care — tarifas máximas e subsídios

=== REGRAS DE CONDUTA ===
1. CONFIDENCIALIDADE: nunca mencione informações de outros usuários ou conversas anteriores.
2. Sempre diga quando não tiver certeza — indique que o usuário confirme com profissional (contador, advogado trabalhista) quando necessário.
3. Para questões de regulação, sempre recomende verificar com Alberta Children's Services para casos específicos.
4. Não tome decisões financeiras ou jurídicas — oriente, não decida.
5. Seja empático e apoiador — gestores de creche têm muito na cabeça!
"""

conversation_history: dict[int, list] = {}
client = OpenAI(api_key=OPENAI_API_KEY)


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        logger.warning("ALLOWED_USER_IDS is empty — all users are blocked. Set it in Secrets.")
        return False
    return user_id in ALLOWED_USER_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        logger.warning(f"Unauthorized access attempt from user_id={user_id}")
        return
    conversation_history[user_id] = []
    await update.message.reply_text(
        "👋 Olá! Sou o assistente da escolinha.\n\n"
        "Posso ajudar com:\n"
        "• Payroll e legislação trabalhista (Alberta)\n"
        "• Contabilidade e subsídios\n"
        "• Marketing e comunicação com famílias\n"
        "• Pedagogia Reggio Emilia + Alberta Flight Framework\n"
        "• Regulamentações de child care em Alberta\n"
        "• Desenvolvimento profissional da equipe\n\n"
        "Tudo que conversamos é confidencial. Como posso ajudar?"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return
    conversation_history[user_id] = []
    await update.message.reply_text("🔄 Conversa reiniciada.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("⛔ Acesso não autorizado.")
        return

    user_text = update.message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_text
    })

    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history[user_id]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            messages=messages
        )

        assistant_reply = response.choices[0].message.content

        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_reply
        })

        await update.message.reply_text(assistant_reply)
        logger.info(f"Replied to user_id={user_id}")

    except Exception as e:
        logger.error(f"OpenAI API error for user_id={user_id}: {e}")
        await update.message.reply_text(
            "⚠️ Ocorreu um erro ao processar sua mensagem. Tente novamente."
        )


def main():
    if not ALLOWED_USER_IDS:
        logger.error(
            "ALLOWED_USER_IDS secret is not set or empty. "
            "Add it to Replit Secrets as a comma-separated list of Telegram user IDs, e.g.: 123456789,987654321"
        )

    logger.info(f"Starting bot with {len(ALLOWED_USER_IDS)} allowed user(s)")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
