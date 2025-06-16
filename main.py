from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import time
import telebot
from telebot import types
import datetime
import re
import random
import string
import threading
import requests
API_TOKEN = '7983424898:AAGjKmtUBCL5H-ecT9F3_631xLJT_J7eS_c' # Make sure this is correctly closed with a single quote
bot = telebot.TeleBot(API_TOKEN)
ADMIN_ID = [6915752059]
from datetime import datetime, timedelta


now = datetime.now() + timedelta(days=0)

ngay = now.day
thang = now.month
nam = now.year

# --- Existing functions (read_wfkey_data, write_wfkey_data, log_admin_action, get_name_from_uid, generate_random_key, etc.) ---
def read_wfkey_data():
    data = {}
    try:
        with open("wfkey.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.strip().split(" | ")]
                if len(parts) >= 4:
                    key = parts[0]
                    hsd = parts[1]
                    hwid = parts[2] if len(parts) > 2 else '0'
                    status = parts[3] if len(parts) > 3 else 'Chưa kích hoạt'
                    lock_status = parts[4] if len(parts) > 4 else 'unlock'
                    uids_str = parts[5] if len(parts) > 5 else ''
                    uids = [u.strip() for u in uids_str.split(",")] if uids_str else []
                    data[key] = {
                        "hsd": hsd,
                        "hwid": hwid,
                        "status": status,
                        "lock_status": lock_status,
                        "uids": uids
                    }
    except FileNotFoundError:
        pass
    return data

def write_wfkey_data(data):
    with open("wfkey.txt", "w", encoding="utf-8") as f:
        for key, value in data.items():
            uids_str = ",".join(value["uids"])
            f.write(f"{key} | {value['hsd']} | {value['hwid']} | {value['status']} | {value['lock_status']} | {uids_str}\n")


def log_admin_action(action_description):
    now = datetime.now()
    timestamp = now.strftime("[%H:%M:%S %d/%m]")
    with open("lsa.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {action_description}\n")

def get_name_from_uid(uid):
    # You might want to fetch the actual user's name from Telegram if possible,
    # but for now, this placeholder is fine.
    return f"User_{uid}"

def generate_random_key():
    random_digits = ''.join(random.choices(string.digits, k=8))
    return f"ZzzRandom_Alpha{random_digits}"

@bot.message_handler(commands=['start'])
def _(message):
    name = message.from_user.first_name or "bạn"
    user_id = message.from_user.id

    caption = (
        f'🤖 <b>Xin Chào Bạn <a href="tg://user?id={user_id}">{name}</a>!</b>\n\n'
        '<blockquote>Tôi Là Dự ĐoánXocdia88! Tôi Là Trợ Lý Alpha Được Tạo Bởi Một Thế Lực Wicked Đằng Sau Nó '
        'Và Tạo Bởi Các Người Đẹp Trai Nhất Thế Giới Giúp Bạn Kéo Về Nhà Sau 1 Tiếng Bế Bot. Chúng Tôi Hỗ Trợ Được Rất Nhiều Sàn. '
        'Dự ĐoánXocdia88 Cập Nhật Liên Tục Nên Bạn Có Thể Yên Tâm, Giá Lại Rất Hạt Dẻ</blockquote>\n\n'
        '<b>🐔 Hãy Sử Dụng Lệnh /whelp Để Có Một Trải Nghiệm Tuyệt Vời</b>'
    )

    video_url = "https://files.catbox.moe/qd4ypc.mp4"
    bot.send_video(
        chat_id=message.chat.id,
        video=video_url,
        caption=caption,
        parse_mode='HTML'
    )


@bot.message_handler(commands=['wkey'])
def handle_wkey(message):
    if message.chat.type != "private":
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Vui Lòng Nhắn Tin Riêng Với Bot Để Sử Dụng Lệnh Này</b>",
            parse_mode='HTML'
        )
        return
    args = message.text.strip().split()
    uid = str(message.from_user.id)
    current_datetime_str = datetime.now().strftime("%m-%d-%Y %H:%M") # Use full datetime for comparison
    data = read_wfkey_data()

    user_key = None
    for k, v in data.items():
        if uid in v["uids"]:
            user_key = k
            break

    if len(args) == 1:
        if not user_key:
            bot.reply_to(message, "Vui Lòng Nhập /wkey + [Key]")
            return
        key_data = data[user_key]

        # Check expiration with datetime
        hsd_datetime = datetime.strptime(key_data["hsd"], "%m-%d-%Y %H:%M")
        if hsd_datetime < datetime.now():
            key_data["uids"] = []
            key_data["status"] = "Hết hạn" # Update status to reflect expiration
            write_wfkey_data(data)
            bot.reply_to(message, "Key Này Đã Hết Hạn Vui Lòng Liên Hệ Admin Để Gia Hạn Thêm")
            return

        if key_data["lock_status"].lower() == "lock":
            bot.reply_to(message, "Key Đã Bị Ban Vui Lòng Liên Hệ Admin Để Biết Thêm Chi Tiết")
            return
        send_key_info(message.chat.id, user_key, key_data, uid in key_data["uids"])
        return

    elif len(args) == 2:
        key_input = args[1]
        if key_input not in data:
            bot.reply_to(message, "Key Không Tồn Tại Liên Hệ Admin Để Mua")
            return
        key_data = data[key_input]

        # Check expiration with datetime
        hsd_datetime = datetime.strptime(key_data["hsd"], "%m-%d-%Y %H:%M")
        if hsd_datetime < datetime.now():
            key_data["uids"] = []
            key_data["status"] = "Hết hạn" # Update status to reflect expiration
            write_wfkey_data(data)
            bot.reply_to(message, "Key Này Đã Hết Hạn Vui Lòng Liên Hệ Admin Để Gia Hạn Thêm")
            return

        if key_data["lock_status"].lower() == "lock":
            bot.reply_to(message, "Key Đã Bị Ban Vui Lòng Liên Hệ Admin Để Biết Thêm Chi Tiết")
            return

        # If hwid is not '0' and it's already full
        if key_data["hwid"] != '0' and int(key_data["hwid"]) <= 0 and uid not in key_data["uids"]:
            bot.reply_to(message, f"🤖 Key {key_input} Đã Đầy Thiết Bị")
            return

        if uid not in key_data["uids"]:
            key_data["uids"].append(uid)
            if key_data["hwid"] != '0': # Only decrement if hwid is not unlimited
                key_data["hwid"] = str(int(key_data["hwid"]) - 1)
            key_data["status"] = "Đã kích hoạt" # Mark as activated upon first successful use
            write_wfkey_data(data)
            log_admin_action(f"[{uid}] Kích hoạt Key {key_input}")

        send_key_info(message.chat.id, key_input, key_data, True)
        return

    else:
        bot.reply_to(message, "Sai cú pháp! Vui lòng nhập /wkey hoặc /wkey [Key]")

def send_key_info(chat_id, key, key_data, show_logout=False):
    msg = (
        "┌─┤Thông Tin WanKey├──⭓\n"
        f"├Key : <tg-spoiler>{key}</tg-spoiler>\n"
        f"├Hwid Devices: {key_data['hwid']} {'(Không giới hạn)' if key_data['hwid'] == '0' else ''}\n"
        f"├Expire Date : {key_data['hsd']}\n"
        f"├Status : {key_data['status']}\n"
        f"├Ban : {('Đã Bị Ban' if key_data['lock_status'].lower() == 'lock' else 'Chưa Bị Ban')}\n"
        "└───────────────⭓"
    )
    if show_logout:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Đăng Xuất", callback_data=f"logout_{key}"))
        bot.send_message(chat_id, msg, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(chat_id, msg, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("logout_"))
def handle_logout(call):
    key = call.data.split("_", 1)[1]
    uid = str(call.from_user.id)
    data = read_wfkey_data()

    if key in data and uid in data[key]["uids"]:
        data[key]["uids"].remove(uid)
        if data[key]["hwid"] != '0': # Only increment if hwid is not unlimited
            data[key]["hwid"] = str(int(data[key]["hwid"]) + 1)
        write_wfkey_data(data)
        bot.answer_callback_query(call.id, "Đăng xuất thành công!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"Bạn đã đăng xuất khỏi key {key}")
    else:
        bot.answer_callback_query(call.id, "Không thể đăng xuất.")

@bot.message_handler(commands=['whelp'])
def send_help(message):
    from datetime import datetime
    now = datetime.now()
    # weekday() trả về 0 (Thứ Hai) đến 6 (Chủ Nhật), nên mảng phải sắp đúng
    thu = ['Hai', 'Ba', 'Tư', 'Năm', 'Sáu', 'Bảy', 'Chủ Nhật'][now.weekday()]
    ngay = now.day
    thang = now.month
    nam = now.year

    user_id = message.from_user.id
    user_name = message.from_user.first_name

    text = f"""
<b>Xin chào bạn <a href="tg://user?id={user_id}">{user_name}</a>, tôi là Dự ĐoánXocdia88 - Tập đoàn của Wicked</b>

📆 Hôm nay là: Th.{thu} {ngay}/{thang}/{nam}
🆔 ID của bạn <a href="tg://user?id={user_id}">{user_name}</a>: <code>{user_id}</code>

<blockquote>
» /wfox + Dự đoán T/X theo cầu 70-80
» /wkey + [Nhập/Login Key để sử dụng]
» /giakey + [Xem bảng giá Key]
» /admin + [Chi tiết Admin]
» /taokey + [Tạo key cho người dùng] <--- NEW COMMAND
</blockquote>

📬 <b>Hãy sử dụng dịch vụ của Dự ĐoánXocdia88, sẽ không làm bạn thất vọng!</b>
"""
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['giakey'])
def gia(message):
    try:
        waiting_msg = bot.send_message(
            message.chat.id,
            "<b>Hãy Đợi Một Chút Nhé Chúng Tôi Không Để Bạn Chờ Lâu</b> ...",
            parse_mode="HTML"
        )

        response = requests.get("https://api.ffcommunity.site/randomvideo.php")
        data = response.json()
        video_url = data['url']

        caption = (
            "🔎 <b>Hãy Xem Seller Dưới Đây Phù Hợp Vui Túi Tiền Của Mình Nhé</b>\n\n"
            "<blockquote>┌ SELLER WKEY Dự ĐoánXocdia88\n"
            "├ 1 NGÀY : 20K\n"
            "├ 1 TUẦN : 50K\n"
            "├ 1 THÁNG : 150K\n"
            "├ 6 THÁNG : 350K\n"
            "├ VĨNH VIỄN : 600K\n"
            "└────────────</blockquote>\n\n"
            "🚫 <b>Lưu Ý : Vui Lòng Mua Ở Các Admin Dự ĐoánXocdia88 Alpha Không Nên Mua Ở Người Khác Mất Tiền Tự Chịu</b>"
        )
        bot.send_video(
            message.chat.id,
            video_url,
            caption=caption,
            parse_mode="HTML",
        )
        bot.delete_message(chat_id=message.chat.id, message_id=waiting_msg.message_id)

    except Exception as e:
        bot.send_message(message.chat.id, f"😥 Oops! Hãy Chạy Lại Lệnh /giakey Lỗi: {e}")

@bot.message_handler(commands=['wfox'])
def wfox_dudoan(message):
    if message.chat.type != "private":
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Vui Lòng Nhắn Tin Riêng Với Bot Để Sử Dụng Lệnh Này</b>",
            parse_mode='HTML'
        )
        return

    user_id = str(message.from_user.id)
    wfkey_data = read_wfkey_data()

    # Tìm key của người dùng
    user_key = None
    for key, value in wfkey_data.items():
        if user_id in value.get("uids", []):
            user_key = key
            break

    if user_key is None:
        # Người dùng chưa có key
        bot.send_message(
            message.chat.id,
            "<b>Bạn Chưa Có Key!</b> Vui lòng mua key hoặc tham gia các event để nhận key miễn phí.",
            parse_mode='HTML'
        )
    else:
        key_info = wfkey_data[user_key]

        # Check trạng thái bị ban (using lock_status for consistency)
        if key_info.get("lock_status", "unlock").lower() == "lock":
            bot.send_message(
                message.chat.id,
                "<b>Bạn đã bị ban!</b> Vui lòng liên hệ Admin để biết thêm chi tiết.",
                parse_mode='HTML'
            )
        else:
            # Kiểm tra hạn sử dụng
            try:
                # Expecting format "MM-DD-YYYY HH:MM"
                hsd_datetime = datetime.strptime(key_info["hsd"], "%m-%d-%Y %H:%M")
                if hsd_datetime < datetime.now():
                    # Key đã hết hạn, xóa tất cả uid và cập nhật trạng thái
                    key_info["uids"] = []
                    key_info["status"] = "Hết hạn"
                    write_wfkey_data(wfkey_data)
                    bot.send_message(
                        message.chat.id,
                        "<b>Key của bạn đã hết hạn!</b> Vui lòng gia hạn hoặc mua key mới.",
                        parse_mode='HTML'
                    )
                else:
                    # Key còn hạn và không bị ban, hiển thị menu chọn sàn
                    markup = types.InlineKeyboardMarkup()
                    xocdia_button = types.InlineKeyboardButton("XocDia88", callback_data="xocdia88")
                    sumclub_button = types.InlineKeyboardButton("SumClub", callback_data="sumclub")
                    markup.add(xocdia_button, sumclub_button)

                    bot.send_message(
                        message.chat.id,
                        f"<b>🎃 Xin Chào Đại Gia {message.from_user.first_name}! Dự ĐoánXocdia88 Được Cập Nhật Thường Xuyên Nên Quý Khách Yên Tâm Sử Dụng </b>\n\n"
                        "<blockquote>🔇 Lưu Ý : Dự ĐoánXocdia88 Chỉ Hỗ Trợ 2 Sàn Casino XocDia88 Và SumClub Để Có Một Trải Nghiệm Tuyệt Vời Cho Đại Gia Chúng Tôi Không Đảm Bảo Kết Quả Đến 100% Nhưng Chúng Tôi Đảm Bảo Kết Quả Thật Từ 70-80% Và Thuật Toán Chuyên Dự Đoán Phiên Đến 1000 Phiên Và Tâm Huyết Nên Quý Khách Tâm Huyết 🎰</blockquote>\n\n"
                        "<b>🀄 Vui Lòng Chọn Sàn Bạn Muốn Chơi Bằng Cách Nhấn Button Bên Dưới :</b>",
                        parse_mode='HTML',
                        reply_markup=markup
                    )
            except ValueError:
                # Xử lý trường hợp định dạng HSD không đúng
                bot.send_message(
                    message.chat.id,
                    "<b>Lỗi định dạng hạn sử dụng key.</b> Vui lòng liên hệ Admin.",
                    parse_mode='HTML'
                )

@bot.callback_query_handler(func=lambda call: call.data == 'xocdia88')
def handle_xocdia88(call):
    try:
        import requests
        from telebot import types

        url = "https://taixiu.system32-cloudfare-356783752985678522.monster/api/luckydice/GetSoiCau?access_token="

        res = requests.get(url)
        if res.status_code != 200:
            raise Exception(f"API lỗi {res.status_code}")

        data = res.json()
        if not isinstance(data, list) or not data:
            raise Exception("Không có dữ liệu")

        lst = data[:10]
        chuoi = ""
        tong_all = 0
        so_5_6 = 0
        xu_huong = []
        du_doan_truoc = ""
        thang = 0
        thua = 0
        reclycle_diff = []
        list_ketqua = []
        xu_huong_seq = []

        for i in lst:
            dice_sum = i["DiceSum"]
            tong_all += dice_sum
            ket_qua = "X" if dice_sum <= 10 else "T"
            chuoi += ket_qua
            list_ketqua.append(ket_qua)

            if du_doan_truoc:
                if ket_qua == du_doan_truoc:
                    thang += 1
                else:
                    thua += 1

            du_doan_truoc = ket_qua

            dices = [i["FirstDice"], i["SecondDice"], i["ThirdDice"]]
            so_5_6 += sum(1 for d in dices if d in [5, 6])

            if len(xu_huong) > 0:
                xu_huong.append(dice_sum - xu_huong[-1])
                reclycle_diff.append(abs(dice_sum - xu_huong[-1]))
            else:
                xu_huong.append(dice_sum)

            if len(xu_huong) >= 3:
                xu_huong_seq.append(tuple(xu_huong[-3:]))

        trung_binh = tong_all / 10
        du_doan = "T" if trung_binh > 10.5 else "X"

        tang = sum(1 for i in xu_huong[1:] if i > 0)
        giam = sum(1 for i in xu_huong[1:] if i < 0)

        ti_le_5_6 = so_5_6 / 30

        dao_dong = sum(1 for i in reclycle_diff if i >= 2)
        reclycle_score = 1 if dao_dong <= 3 else 0

        last_dice = data[0]["DiceSum"]
        bliplack_score = 1 if last_dice in [5, 7, 13, 11] or str(last_dice)[0] == str(last_dice)[-1] else 0

        count_1 = sum(i["FirstDice"] == 1 or i["SecondDice"] == 1 or i["ThirdDice"] == 1 for i in lst)
        count_3 = sum(i["FirstDice"] == 3 or i["SecondDice"] == 3 or i["ThirdDice"] == 3 for i in lst)
        dicerefund_score = 1 if (count_1 + count_3) >= 9 else 0

        count_t = list_ketqua.count("T")
        count_x = list_ketqua.count("X")
        becau_score = 1 if abs(count_t - count_x) <= 2 else 0

        score = 0
        if trung_binh > 10.5:
            score += 1
        if tang > giam:
            score += 1
        if ti_le_5_6 > 0.4:
            score += 1
        score += reclycle_score + bliplack_score + dicerefund_score + becau_score

        raw_score = int((score / 7) * 100)
        ti_le = max(60, min(raw_score, 90))
        if ti_le >= 70:
            ti_le_text = f"{ti_le}% - Cược Lớn Auto Húp All-in Luôn"
        elif ti_le >= 60:
            ti_le_text = f"{ti_le}% - Cược Vừa Để Mất Tránh Tiêc "
        else:
            ti_le_text = f"{ti_le}% - Cược Nhẹ Làm Nhử "

        theo_cau = du_doan

        force_tai = False
        if last_dice in [15, 16, 17, 18] and not xu_huong:
            force_tai = True

        if force_tai:
            theo_cau = "T"
        else:
            if xu_huong_seq:
                last_seq = xu_huong_seq[-1]
                if last_seq == (2, 1, 2):
                    theo_cau = "X"
                elif last_seq == (1, 2, 3):
                    theo_cau = "T"
                elif last_seq == (3, 2, 1):
                    theo_cau = "X"

            if 11 <= last_dice <= 13:
                theo_cau = "X"

        phien = int(data[0]["SessionId"]) + 1

        nd = f"""
<b>🔇 Xin Chào Người Đẹp ! Hãy Làm Vài Tay Để Dự ĐoánXocdia88 Alpha Kéo Bạn Về Bờ Hãy Làm Vài Tay Nào !</b>

<blockquote>🔎<b> Phân Tích Phiên #<b>{phien}</b></b>

📭 10 Phiên Gần Nhất: <b>{chuoi}</b>

🔖 Dự Đoán: <b>{theo_cau}</b>

📊 Tỷ Lệ: {ti_le_text}</blockquote>

<b>[ T ] là Tài, [ X ] là Xỉu Nên Lưu Ý Chọn Đúng Cược Nhen</b>
"""
        web_app_url = 'https://play.xocdia88.it.com'

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='XocDia 88', url=web_app_url))
        markup.add(types.InlineKeyboardButton(text='🔄 Reload', callback_data='xocdia88'))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=nd,
                parse_mode="HTML",
                reply_markup=markup
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                raise e

    except Exception as e:
        import traceback
        traceback.print_exc()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Lỗi: {str(e)}"
        )

@bot.callback_query_handler(func=lambda call: call.data == 'sumclub')
def handle_sumclub(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Chưa Cập Nhật Sàn *SumClub*!", parse_mode="Markdown")

@bot.message_handler(commands=['akey'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_akey(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Random", callback_data="akey_random"),
               types.InlineKeyboardButton("Thường", callback_data="akey_normal"))
    bot.send_message(message.chat.id, "Chọn cách tạo key:", reply_markup=markup)

@bot.message_handler(commands=['ekey'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_ekey(message):
    try:
        key_to_edit = message.text.split(" ", 1)[1].strip()
        data = read_wfkey_data()

        if key_to_edit not in data:
            bot.send_message(message.chat.id, f"Không tìm thấy **Key**: `{key_to_edit}`", parse_mode="Markdown")
            return

        key_info = data[key_to_edit]
        hwid_display = "Chưa có" if key_info['hwid'] == '0' or not key_info['hwid'] else key_info['hwid']

        response_text = (
            f"<blockquote>┌───────────\n"
            f"├─ Key : <tg-spoiler>{key_to_edit}</tg-spoiler>\n"
            f"├─ Hwid : {hwid_display}\n"
            f"├─ Kích Hoạt : {key_info['status']}\n"
            f"├─ Ban : {key_info['lock_status']}\n"
            f"├─ HSD : {key_info['hsd']}\n"
            f"└───────────</blockquote>\n\n"
            f"🤖 Pixel quảng cáo nè: Hãy mua VIP để sử dụng ngon hơn nhé :>"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        lock_btn_text = "UnBan" if key_info['lock_status'] == "lock" else "Ban"

        # Thêm nút theo hàng 2 cột
        markup.add(
            types.InlineKeyboardButton("Edit Expire", callback_data=f"ekey_edit_exp_{key_to_edit}"),
            types.InlineKeyboardButton(lock_btn_text, callback_data=f"ekey_toggle_ban_{key_to_edit}")
        )
        markup.add(
            types.InlineKeyboardButton("Hwid", callback_data=f"ekey_hwid_list_{key_to_edit}"),
            types.InlineKeyboardButton("Del Key", callback_data=f"ekey_del_key_{key_to_edit}")
        )

        bot.send_message(message.chat.id, response_text, reply_markup=markup, parse_mode="HTML")

    except IndexError:
        bot.send_message(message.chat.id, "Vui lòng nhập Key theo định dạng: `/ekey [Key]`", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.from_user.id in ADMIN_ID)
def callback_query(call):
    parts = call.data.split("_")
    action_group = parts[0] + "_" + parts[1]
    key = parts[-1] if len(parts) > 2 else None
    data = read_wfkey_data()

    if action_group == "ekey_edit":
        bot.send_message(call.message.chat.id, "Vui lòng Nhập Hạn Sử Dụng Muốn Trừ Hoặc Cộng (Ví Dụ: Nếu Trừ Thì `-1`, Còn Cộng Thì `1`). **Định dạng HSD sẽ là MM-DD-YYYY HH:MM.**", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_edit_expire_input(m, key))

    elif action_group == "ekey_toggle":
        if key in data:
            new_status = "unlock" if data[key]["lock_status"] == "lock" else "lock"
            data[key]["lock_status"] = new_status
            write_wfkey_data(data)
            status_text = "UnBan" if new_status == "unlock" else "Ban"
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"Đã **{status_text}** Key `{key}`", parse_mode="Markdown")
            log_admin_action(f"[{status_text.upper()}] Đã {status_text} Key {key}")

    elif action_group == "ekey_hwid":
        if key in data:
            uids = data[key]["uids"]
            hwid_list_text = f"**Danh Sách Hwid Cho Key** `{key}`:\n\n"
            if uids:
                for uid in uids:
                    hwid_list_text += f"<blockquote>{uid} - {get_name_from_uid(uid)}</blockquote>\n"
            else:
                hwid_list_text += "Key này chưa có Hwid nào."

            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("Del User", callback_data=f"ekey_del_user_{key}"),
                types.InlineKeyboardButton("Add Hwid", callback_data=f"ekey_add_hwid_{key}")
            )
            markup.add(types.InlineKeyboardButton("Del Hwid", callback_data=f"ekey_del_hwid_{key}"))

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=hwid_list_text, reply_markup=markup, parse_mode="HTML")

    elif action_group == "ekey_del":
        if key in data:
            del data[key]
            write_wfkey_data(data)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"Đã **Xóa Key** `{key}`", parse_mode="Markdown")
            log_admin_action(f"[DEL] Đã Xóa Key {key}")

    elif action_group == "ekey_del_user":
        bot.send_message(call.message.chat.id, "Vui Lòng Nhập **UID** Muốn Xóa:", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_del_user_input(m, key))

    elif action_group == "ekey_add_hwid":
        bot.send_message(call.message.chat.id, "Vui Lòng Nhập **Số Hwid** Muốn Thêm:", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_add_hwid_input(m, key))

    elif action_group == "ekey_del_hwid":
        bot.send_message(call.message.chat.id, "Vui Lòng Nhập **Số Hwid** Muốn Xóa:", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, lambda m: _ekey_del_hwid_input(m, key))

    elif action_group == "akey_random":
        bot.send_message(call.message.chat.id, "Vui lòng nhập **Số Lượng Key** | **Số Ngày HSD** | **Số HWID (0 nếu không giới hạn)** (ví dụ: `5 | 30 | 1`)", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, _akey_random_input)

    elif action_group == "akey_normal":
        # Changed instructions for _akey_normal_input
        bot.send_message(call.message.chat.id, "Vui lòng nhập **Tên Key** | **ID Người Chơi** | **Ngày Hết Hạn (MM-DD-YYYY)** | **Giờ Hết Hạn (HH:MM)** (ví dụ: `MyKey123 | 123456789 | 12-31-2025 | 23:59`)", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, _akey_normal_input)

    elif action_group == "ls_admin":
        try:
            with open("lsa.txt", "r", encoding="utf-8") as f:
                history_content = f.read()
            text_to_send = f"**Lịch Sử Admin**:\n\n`{history_content}`" if history_content else "Lịch Sử Admin trống."
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text_to_send, parse_mode="Markdown")
        except FileNotFoundError:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="File `lsa.txt` không tồn tại.", parse_mode="Markdown")

    elif action_group == "ls_user":
        try:
            with open("lsu.txt", "r", encoding="utf-8") as f:
                history_content = f.read()
            text_to_send = f"**Lịch Sử User**:\n\n`{history_content}`" if history_content else "Lịch Sử User trống."
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=text_to_send, parse_mode="Markdown")
        except FileNotFoundError:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="File `lsu.txt` không tồn tại.", parse_mode="Markdown")


@bot.message_handler(commands=['ls'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_ls(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Lịch Sử Admin", callback_data="ls_admin"),
               types.InlineKeyboardButton("Lịch Sử User", callback_data="ls_user"))
    bot.send_message(message.chat.id, "Chọn lịch sử muốn xem:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.from_user.id in ADMIN_ID)
def callback_query(call):
    parts = call.data.split("_")
    action_group = parts[0] + "_" + parts[1]

    if action_group == "ls_admin":
        try:
            with open("lsa.txt", "r", encoding="utf-8") as f:
                history_content = f.read()
            text_to_send = (
                f"<b>Lịch Sử Admin</b>:\n\n<blockquote>{history_content}</blockquote>"
                if history_content else "Lịch Sử Admin trống."
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text_to_send,
                parse_mode="HTML"
            )
        except FileNotFoundError:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="File `lsa.txt` không tồn tại.",
                parse_mode="Markdown"
            )

    elif action_group == "ls_user":
        try:
            with open("lsu.txt", "r", encoding="utf-8") as f:
                history_content = f.read()
            text_to_send = (
                f"<b>Lịch Sử User</b>:\n\n<blockquote>{history_content}</blockquote>"
                if history_content else "Lịch Sử User trống."
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text_to_send,
                parse_mode="HTML"
            )
        except FileNotFoundError:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="File `lsu.txt` không tồn tại.",
                parse_mode="Markdown"
            )

def _ekey_edit_expire_input(message, key):
    try:
        # Expecting MM-DD-YYYY HH:MM format for new expiry
        new_hsd_str = message.text.strip()
        new_hsd_datetime = datetime.strptime(new_hsd_str, "%m-%d-%Y %H:%M")
        data = read_wfkey_data()
        if key in data:
            data[key]["hsd"] = new_hsd_datetime.strftime("%m-%d-%Y %H:%M")
            write_wfkey_data(data)
            bot.send_message(message.chat.id, f"Đã cập nhật **HSD** cho Key `{key}` thành `{data[key]['hsd']}`", parse_mode="Markdown")
            log_admin_action(f"[EDIT EXP] Key {key} HSD mới: {data[key]['hsd']}")
        else:
            bot.send_message(message.chat.id, f"Không tìm thấy Key: `{key}`", parse_mode="Markdown")
    except ValueError:
        bot.send_message(message.chat.id, "Định dạng HSD hoặc giá trị nhập vào không hợp lệ. Vui lòng nhập đúng định dạng `MM-DD-YYYY HH:MM`.", parse_mode="Markdown")

def _ekey_del_user_input(message, key):
    uid_to_delete = message.text.strip()
    data = read_wfkey_data()
    if key in data:
        if uid_to_delete in data[key]["uids"]:
            data[key]["uids"].remove(uid_to_delete)
            # If hwid is not '0' (unlimited), increment it back
            if data[key]["hwid"] != '0':
                data[key]["hwid"] = str(int(data[key]["hwid"]) + 1)
            write_wfkey_data(data)
            bot.send_message(message.chat.id, f"Đã xóa **UID** `{uid_to_delete}` khỏi Key `{key}`.", parse_mode="Markdown")
            log_admin_action(f"[DEL USER] Đã xóa UID {uid_to_delete} khỏi Key {key}")
        else:
            bot.send_message(message.chat.id, f"Không tìm thấy **UID** `{uid_to_delete}` trong Key `{key}`.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"Không tìm thấy Key: `{key}`", parse_mode="Markdown")

def _ekey_add_hwid_input(message, key):
    uid_to_add = message.text.strip() # Renamed to uid_to_add for clarity
    data = read_wfkey_data()
    if key in data:
        if uid_to_add not in data[key]["uids"]:
            data[key]["uids"].append(uid_to_add)
            data[key]["status"] = "Đã kích hoạt"

            # If hwid is not '0' (unlimited), decrement it
            if data[key]["hwid"] != '0':
                data[key]["hwid"] = str(int(data[key]["hwid"]) - 1)

            # If HSD is "Chưa kích hoạt" or needs to be set, set it to current time
            if data[key]["hsd"] == "Chưa kích hoạt" or not data[key]["hsd"].strip():
                data[key]["hsd"] = datetime.now().strftime("%m-%d-%Y %H:%M") # Set to current datetime

            write_wfkey_data(data)
            bot.send_message(message.chat.id, f"Đã thêm **UID** `{uid_to_add}` vào Key `{key}`. Key đã được kích hoạt. HSD: `{data[key]['hsd']}`.", parse_mode="Markdown")
            log_admin_action(f"[ADD HWID] Đã thêm UID {uid_to_add} vào Key {key}. Key kích hoạt.")
        else:
            bot.send_message(message.chat.id, f"**UID** `{uid_to_add}` đã tồn tại trong Key `{key}`.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"Không tìm thấy Key: `{key}`", parse_mode="Markdown")

def _ekey_del_hwid_input(message, key):
    uid_to_delete = message.text.strip() # Renamed to uid_to_delete for clarity
    data = read_wfkey_data()
    if key in data:
        if uid_to_delete in data[key]["uids"]:
            data[key]["uids"].remove(uid_to_delete)
            # If hwid is not '0' (unlimited), increment it back
            if data[key]["hwid"] != '0':
                data[key]["hwid"] = str(int(data[key]["hwid"]) + 1)
            write_wfkey_data(data)
            bot.send_message(message.chat.id, f"Đã xóa **UID** `{uid_to_delete}` khỏi Key `{key}`.", parse_mode="Markdown")
            log_admin_action(f"[DEL HWID] Đã xóa UID {uid_to_delete} khỏi Key {key}")
        else:
            bot.send_message(message.chat.id, f"Không tìm thấy **UID** `{uid_to_delete}` trong Key `{key}`.", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"Không tìm thấy Key: `{key}`", parse_mode="Markdown")


def _akey_random_input(message):
    try:
        parts = [p.strip() for p in message.text.split('|')]
        if len(parts) != 3:
            raise ValueError("Định dạng không đúng. Vui lòng nhập: `Số Lượng | Số Ngày HSD | Số HWID`")

        num_keys = int(parts[0])
        hsd_days = int(parts[1])
        hwid_limit = parts[2]

        if not hwid_limit.strip():
            hwid_limit = "0"

        # Calculate expiry based on days from now (current time is also important)
        expiry_datetime = datetime.now() + timedelta(days=hsd_days)
        hsd_calculated = expiry_datetime.strftime("%m-%d-%Y %H:%M")

        generated_keys_info = []
        file_lines = []
        for _ in range(num_keys):
            new_key = generate_random_key()
            key_info = f"{new_key} | {hsd_calculated} | {hwid_limit} | Chưa kích hoạt | unlock"
            generated_keys_info.append(f"<tg-spoiler>{new_key}</tg-spoiler> | HSD: {hsd_calculated} | HWID Limit: {hwid_limit}")
            file_lines.append(key_info)

        # Ghi vào file
        with open("wfkey.txt", "a", encoding="utf-8") as f:
            for line in file_lines:
                f.write(line + "\n")

        response_text = "<b>Danh Sách Key Đã Random (Đã Lưu Vào File)</b>:\n\n" + "\n".join([f"<blockquote>{key_info}</blockquote>" for key_info in generated_keys_info])
        bot.send_message(message.chatm.id, response_text, parse_mode="HTML")
        log_admin_action(f"[GENERATE RANDOM + SAVE] Tạo {num_keys} key ngẫu nhiên và lưu vào file với HSD: {hsd_calculated}, HWID Limit: {hwid_limit}")

    except ValueError as e:
        bot.send_message(message.chat.id, f"Lỗi: {e}\nVui lòng nhập đúng định dạng: `Số Lượng | Số Ngày HSD | Số HWID` (ví dụ: `5 | 30 | 1`)", parse_mode="Markdown")

# NEW COMMAND FOR ADMIN: /taokey
@bot.message_handler(commands=['taokey'], func=lambda message: message.from_user.id in ADMIN_ID)
def handle_taokey(message):
    bot.send_message(message.chat.id, "Vui lòng nhập **Tên Key** | **ID Người Chơi** | **Ngày Hết Hạn (MM-DD-YYYY)** | **Giờ Hết Hạn (HH:MM)** (ví dụ: `MyKey123 | 123456789 | 12-31-2025 | 23:59`)", parse_mode="Markdown")
    bot.register_next_step_handler(message, _process_taokey_input)

def _process_taokey_input(message):
    try:
        parts = [p.strip() for p in message.text.split('|')]
        if len(parts) != 4:
            raise ValueError("Định dạng không đúng. Vui lòng nhập: `Tên Key | ID Người Chơi | Ngày Hết Hạn (MM-DD-YYYY) | Giờ Hết Hạn (HH:MM)`")

        new_key = parts[0]
        user_id_to_assign = parts[1]
        expiry_date_str = parts[2]
        expiry_time_str = parts[3]

        if not new_key:
            raise ValueError("Tên key không được để trống.")
        if not user_id_to_assign.isdigit():
            raise ValueError("ID Người Chơi phải là số.")

        # Combine date and time
        expiry_datetime_str = f"{expiry_date_str} {expiry_time_str}"
        expiry_datetime_obj = datetime.strptime(expiry_datetime_str, "%m-%d-%Y %H:%M")
        hsd_calculated = expiry_datetime_obj.strftime("%m-%d-%Y %H:%M")

        data = read_wfkey_data()
        if new_key in data:
            bot.send_message(message.chat.id, f"Key `{new_key}` đã tồn tại. Vui lòng chọn tên khác.", parse_mode="Markdown")
            return

        # Check if the UID is already assigned to another active key
        for key, value in data.items():
            if user_id_to_assign in value.get("uids", []) and datetime.strptime(value["hsd"], "%m-%d-%Y %H:%M") > datetime.now() and value["lock_status"].lower() != "lock":
                bot.send_message(message.chat.id, f"ID Người Chơi `{user_id_to_assign}` đã được gán cho Key `{key}` và đang hoạt động. Vui lòng gỡ bỏ trước hoặc tạo key mới cho UID khác.", parse_mode="Markdown")
                return


        data[new_key] = {
            "hsd": hsd_calculated,
            "hwid": "0", # Set to unlimited for manually assigned keys, or you can ask for a limit
            "status": "Đã kích hoạt", # Automatically activated since a user ID is assigned
            "lock_status": "unlock",
            "uids": [user_id_to_assign]
        }
        write_wfkey_data(data)
        bot.send_message(message.chat.id,
                         f"Đã tạo **Key** `{new_key}` và gán cho **UID** `{user_id_to_assign}`. HSD: `{hsd_calculated}`. Trạng thái: **Đã kích hoạt**.",
                         parse_mode="Markdown")
        log_admin_action(f"[CREATE KEY FOR USER] Tạo Key {new_key} cho UID {user_id_to_assign} với HSD: {hsd_calculated}")

    except ValueError as e:
        bot.send_message(message.chat.id, f"Lỗi: {e}\nVui lòng nhập đúng định dạng: `Tên Key | ID Người Chơi | Ngày Hết Hạn (MM-DD-YYYY) | Giờ Hết Hạn (HH:MM)`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"Đã xảy ra lỗi không mong muốn: {e}", parse_mode="Markdown")


def get_bot_info():
    try:
        me = bot.get_me()
        print(f"NAME BOT : {me.first_name}")
        print(f"Username : @{me.username}")
    except Exception as e:
        print("Lỗi khi lấy thông tin bot:", e)

def polling_with_retry():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Lỗi khi polling:", e)
            print("Đang thử lại sau 5 giây...")
            time.sleep(5)

if __name__ == "__main__":
    get_bot_info()
    polling_thread = threading.Thread(target=polling_with_retry)
    polling_thread.start()


