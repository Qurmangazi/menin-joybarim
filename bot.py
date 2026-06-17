import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from sut_data import PRODUCTS, CATEGORIES

# BotFather orqali olingan tokenni API_TOKEN o'rniga yozing
API_TOKEN = "8488765620:AAFqRepAksK_4FKFu-HERBYTZST1I6PlLHw"

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Foydalanuvchi savatchasi (vaqtinchalik xotirada, production uchun DB kerak)
user_carts = {}

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Mahsulotlar"), KeyboardButton(text="🛒 Savatcha")],
            [KeyboardButton(text="📞 Biz bilan bog'lanish"), KeyboardButton(text="ℹ️ Ma'lumot")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_categories_keyboard():
    buttons = []
    for cat_id, cat_name in CATEGORIES.items():
        buttons.append([InlineKeyboardButton(text=cat_name, callback_data=f"cat_{cat_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    await message.answer(
        "Assalomu alaykum! **SutBozor** botiga xush kelibsiz! 🥛\n\n"
        "Bu yerda siz toza va tabiiy sut mahsulotlarini buyurtma qilishingiz mumkin.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "🛍 Mahsulotlar")
async def show_categories(message: Message):
    await message.answer("Kategoriyani tanlang:", reply_markup=get_categories_keyboard())

@dp.callback_query(F.data.startswith("cat_"))
async def show_products_by_category(callback: CallbackQuery):
    cat_id = callback.data.split("_")[1]
    category_products = [p for p in PRODUCTS if p["cat"] == cat_id]
    
    if not category_products:
        await callback.answer("Ushbu kategoriyada mahsulotlar topilmadi.")
        return

    await callback.message.edit_text(f"**{CATEGORIES[cat_id]}** mahsulotlari:", parse_mode="Markdown")
    
    for p in category_products:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Savatchaga qo'shish", callback_data=f"add_{p['id']}")]
        ])
        
        text = (
            f"{p['emoji']} **{p['name']}**\n"
            f"💰 Narxi: {p['price']:,} so'm / {p['unit']}\n"
            f"📝 {p['desc']}"
        )
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await callback.answer()

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if product:
        user_carts[user_id].append(product)
        await callback.answer(f"✅ {product['name']} savatchaga qo'shildi!")
    else:
        await callback.answer("Xatolik: Mahsulot topilmadi.")

@dp.message(F.text == "🛒 Savatcha")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        await message.answer("Savatchangiz bo'sh. 🛒")
        return

    total_price = sum(p["price"] for p in cart)
    cart_text = "🛒 **Sizning savatchangiz:**\n\n"
    
    # Mahsulotlarni sanash
    from collections import Counter
    counts = Counter(p["id"] for p in cart)
    
    for p_id, count in counts.items():
        p = next(p for p in PRODUCTS if p["id"] == p_id)
        cart_text += f"🔹 {p['name']} - {count} ta x {p['price']:,} = {p['price']*count:,} so'm\n"
    
    cart_text += f"\n💰 **Jami: {total_price:,} so'm**"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart")]
    ])
    
    await message.answer(cart_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_carts[user_id] = []
    await callback.answer("Savatcha tozalandi.")
    await callback.message.edit_text("Savatchangiz bo'sh. 🛒")

@dp.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery):
    await callback.message.answer("Buyurtmangiz qabul qilindi! Tezz orada operatorimiz siz bilan bog'lanadi. ✅")
    user_carts[callback.from_user.id] = []
    await callback.answer()

@dp.message(F.text == "📞 Biz bilan bog'lanish")
async def contact_us(message: Message):
    await message.answer(
        "📞 **Biz bilan bog'lanish:**\n\n"
        "📍 Manzil: Toshkent, Yunusobod, Amir Temur 108\n"
        "📞 Telefon: +998 71 234 56 78\n"
        "📧 Email: info@sutbozor.uz\n"
        "🕐 Ish vaqti: 07:00 – 21:00",
        parse_mode="Markdown"
    )

@dp.message(F.text == "ℹ️ Ma'lumot")
async def about_info(message: Message):
    await message.answer(
        "**SutBozor** — bu toza, tabiiy va yangi sut mahsulotlarini uyingizga yetkazib beruvchi platforma. 🥛🌿\n\n"
        "Barcha mahsulotlarimiz mahalliy fermerlar tomonidan tayyorlanadi va qat'iy sifat nazoratidan o'tadi.",
        parse_mode="Markdown"
    )

async def main():
    print("🚀 SutBozor boti ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot to'xtatildi.")
