from flask import Flask, render_template, request, jsonify, redirect, url_for
from bytez import Bytez
import random

app = Flask(__name__)
app.secret_key = "tarot_secret_key_mystic"

# Cấu hình Bytez SDK
KEY = "229e25528918a3f8bf259a56fed364e6"
sdk = Bytez(KEY)

AI_MODELS = {
    "deep": "anthropic/claude-opus-4-5",
    "balanced": "openai/gpt-4o",
    "fast": "google/gemini-2.5-flash-lite"
}

# Danh sách bài Tarot
TAROT_DECK = []
major_cards = ["The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit", "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance", "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"]
major_emojis = ["🃏", "🪄", "🌙", "👑", "🏛️", "⛪", "❤️", "🛒", "🦁", "🕯️", "🎡", "⚖️", "🙃", "💀", "🍷", "😈", "⚡", "🌟", "🌕", "☀️", "🎺", "🌍"]

for i, name in enumerate(major_cards):
    TAROT_DECK.append({"id": i, "name": name, "emoji": major_emojis[i], "suit": "Major"})

suits = ["Wands", "Cups", "Swords", "Pentacles"]
emojis = {"Wands": "🪄", "Cups": "🏆", "Swords": "⚔️", "Pentacles": "🪙"}
ranks = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Page", "Knight", "Queen", "King"]
for s in suits:
    for r in ranks:
        TAROT_DECK.append({"id": len(TAROT_DECK), "name": f"{r} of {s}", "emoji": emojis[s], "suit": s})

@app.route('/')
def index():
    # Kiểm tra nếu thiếu dấu gạch chéo cuối cùng khi chạy qua dispatcher
    if not request.path.endswith('/'):
        return redirect(request.path + '/')
    return render_template('index.html')

@app.route('/draw', methods=['POST'])
def draw_cards():
    try:
        data = request.json
        deck_type = data.get('deck_type', 'major')
        current_deck = [c for c in TAROT_DECK if c['suit'] == 'Major'] if deck_type == 'major' else TAROT_DECK
        drawn = random.sample(current_deck, 3)
        for card in drawn:
            card['is_reversed'] = random.choice([True, False])
        return jsonify({"cards": drawn})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/read', methods=['POST'])
def get_reading():
    try:
        data = request.json
        question = data.get('question', '')
        cards = data.get('cards', [])
        chat_history = data.get('history', [])
        ai_speed = data.get('ai_speed', 'deep')
        
        model_id = AI_MODELS.get(ai_speed, AI_MODELS["deep"])
        
        cards_desc = [f"{c['name']} ({'Ngược' if c.get('is_reversed') else 'Xuôi'})" for c in cards]
        cards_str = ", ".join(cards_desc)
        
        # System Prompt THÔNG MINH & LINH HOẠT
        system_instruction = """Bạn là một hệ thống diễn giải Tarot chuyên nghiệp.

        NHIỆM VỤ CỐT LÕI:
        Phân tích 3 lá bài Tarot để trả lời câu hỏi của người dùng một cách chính xác, trực tiếp và có ý nghĩa thực tế.
        Không kể chuyện lan man. Không viết văn học. Không triết lý dài.

        NGUYÊN TẮC:
        - Luôn trả lời đúng trọng tâm câu hỏi trước.
        - Mọi nội dung phải liên hệ trực tiếp tới ý nghĩa lá bài.
        - Không được nói chung chung kiểu "vũ trụ", "định mệnh mơ hồ".
        - Không được né câu hỏi.
        - Không được từ chối câu hỏi về tên, chữ cái, người cụ thể — phải suy luận biểu tượng từ lá bài.

        CÁCH DIỄN GIẢI:
        Ba lá bài phải được hiểu theo cấu trúc:
        1. Lá 1 → Quá khứ / Nguyên nhân
        2. Lá 2 → Hiện tại / Tình trạng thực
        3. Lá 3 → Tương lai gần / Kết quả có xu hướng xảy ra

        XỬ LÝ ĐẢO NGƯỢC:
        - Lá xuôi = năng lượng biểu hiện bên ngoài, rõ ràng.
        - Lá ngược = năng lượng bị cản trở, trì hoãn, hiểu sai, che giấu hoặc nội tâm.

        QUY TẮC PHẢN HỒI THEO LOẠI CÂU HỎI:

        [TÌNH YÊU]
        → tập trung người kia nghĩ gì, cảm xúc thật, khả năng tiến triển.

        [SỰ NGHIỆP / HỌC TẬP]
        → tập trung kết quả thực tế, khó khăn, hướng hành động.

        [TÊN / CHỮ CÁI / AI ĐÓ]
        → phải suy luận ký tự dựa trên biểu tượng lá bài (nguyên tố, con số, hình ảnh).
        → đưa 3-6 chữ cái hoặc tên tiếng Việt có khả năng cao.

        [KHÔNG RÕ CÂU HỎI]
        → trước tiên giải thích tình trạng hiện tại của người hỏi.

        ĐỊNH DẠNG BẮT BUỘC:

        ## Tổng quan
        (1-2 câu trả lời thẳng câu hỏi)

        ## Diễn giải từng lá
        ### Lá 1 – ...
        ...
        ### Lá 2 – ...
        ...
        ### Lá 3 – ...
        ...

        ## Kết luận
        (điều có khả năng xảy ra)

        ## Lời khuyên hành động
        (việc cụ thể người hỏi nên làm trong 1-2 tuần tới)

        GIỚI HẠN:
        - 350–550 từ.
        - Không dùng thơ.
        - Không roleplay pháp sư.
        - Không dùng emoji.
        - Không hỏi lại người dùng.
        
        ĐỊNH DẠNG:
        - Dùng Markdown (##, ###, **, >).
        - KHÔNG dùng khung ASCII Art (╔═══╗).
        - Trình bày mạch lạc, sạch sẽ, không quá dài dòng nhưng phải đủ sâu sắc.
        - Các thông điệp quan trọng nên để trong blockquote (>)."""
        
        messages = []
        if not chat_history:
            messages.append({"role": "user", "content": f"{system_instruction}\n\nCâu hỏi: {question}\nCác lá bài đã rút: {cards_str}"})
        else:
            for msg in chat_history:
                messages.append(msg)
            messages.append({"role": "user", "content": f"Tiếp tục trả lời dựa trên ngữ cảnh: {question}"})

        model = sdk.model(model_id)
        results = model.run(messages)
        
        res_output = getattr(results, 'output', results)
        if isinstance(res_output, dict):
            output = res_output.get('content', str(res_output))
        elif isinstance(res_output, list) and len(res_output) > 0:
            item = res_output[0]
            output = item.get('content', str(item)) if isinstance(item, dict) else str(item)
        else:
            output = str(res_output)

        return jsonify({"output": output})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
