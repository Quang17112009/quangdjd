// --- START OF FILE sunfix.js ---

const Fastify = require("fastify");
const cors = require("@fastify/cors");
const WebSocket = require("ws");

const TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhbW91bnQiOjE0MDAsInVzZXJuYW1lIjoiU0Nfbmd1eWVudmFudGluaG5lIn0.owsA4eD0qVYinV3CZcPIu5nLuUVm56ZZmoTRz9WVGW8";

const fastify = Fastify({ logger: false });
const PORT = process.env.PORT || 3001;

let rikWS = null;
let rikIntervalCmd = null;

// =================================================================
// --- STATE & ALGORITHM INITIALIZATION ---
// =================================================================

const MAX_HISTORY_LEN = 200; // Số phiên lịch sử tối đa lưu trữ
const MIN_HISTORY_FOR_PREDICTION = 12; // Số phiên tối thiểu để bắt đầu dự đoán

// Lịch sử kết quả
let rikResults = []; // Lưu object kết quả gốc từ websocket
let history = [];    // Lưu chuỗi kết quả ['Tài', 'Xỉu', ...] để dự đoán
let rikCurrentSession = null;

// State cho các thuật toán
const patterns = define_patterns(); // Các pattern được định nghĩa
let transition_matrix = [[0.5, 0.5], [0.5, 0.5]]; // Ma trận chuyển đổi Markov
let transition_counts = [[1, 1], [1, 1]]; // Số lần chuyển đổi cho Markov (khởi tạo với 1 để tránh chia cho 0)
let logistic_weights = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]; // Trọng số cho Logistic Regression (6 features)
let logistic_bias = 0.0; // Bias cho Logistic Regression
const learning_rate = 0.01; // Tốc độ học
const regularization = 0.01; // Hệ số điều chuẩn

// State cho ensemble model động
const default_model_weights = {
    'pattern': 0.30,
    'markov': 0.10,
    'logistic': 0.15,
    'trend': 0.15,
    'short': 0.10,
    'mean': 0.10,
    'switch': 0.10
};
let model_weights = { ...default_model_weights };
let model_performance = {
  pattern: { success: 0, total: 0 },
  markov: { success: 0, total: 0 },
  logistic: { success: 0, total: 0 },
  trend: { success: 0, total: 0 },
  short: { success: 0, total: 0 },
  mean: { success: 0, total: 0 },
  switch: { success: 0, total: 0 },
};

let overall_performance = { success: 0, total: 0 }; // Hiệu suất tổng thể
let last_prediction = null; // Lưu dự đoán cuối cùng để học
let pattern_accuracy = new Map(); // Hiệu suất của từng pattern

// =================================================================
// --- HELPER & CORE FUNCTIONS ---
// =================================================================

// Binary message decoder
function decodeBinaryMessage(buffer) {
  try {
    const str = buffer.toString();
    if (str.startsWith("[")) {
      return JSON.parse(str);
    }
    let position = 0;
    const result = [];
    while (position < buffer.length) {
      const type = buffer.readUInt8(position++);
      if (type === 1) { // String
        const length = buffer.readUInt16BE(position);
        position += 2;
        const str = buffer.toString('utf8', position, position + length);
        position += length;
        result.push(str);
      } else if (type === 2) { // Number
        const num = buffer.readInt32BE(position);
        position += 4;
        result.push(num);
      } else if (type === 3) { // Object
        const length = buffer.readUInt16BE(position);
        position += 2;
        const objStr = buffer.toString('utf8', position, position + length);
        position += length;
        result.push(JSON.parse(objStr));
      } else if (type === 4) { // Array
        const length = buffer.readUInt16BE(position);
        position += 2;
        const arrStr = buffer.toString('utf8', position, position + length);
        position += length;
        result.push(JSON.parse(arrStr));
      } else {
        console.warn("Unknown binary type:", type);
        break;
      }
    }
    return result.length === 1 ? result[0] : result;
  } catch (e) {
    console.error("Binary decode error:", e);
    return null;
  }
}

function getTX(d1, d2, d3) {
  const sum = d1 + d2 + d3;
  return sum >= 11 ? "T" : "X";
}

function getKetQua(d1, d2, d3) {
    const sum = d1 + d2 + d3;
    return sum >= 11 ? "Tài" : "Xỉu";
}

function sendRikCmd1005() {
  if (rikWS && rikWS.readyState === WebSocket.OPEN) {
    const payload = [6, "MiniGame", "taixiuPlugin", { cmd: 1005 }];
    rikWS.send(JSON.stringify(payload));
  }
}

// =================================================================
// --- PREDICTION ALGORITHMS ---
// =================================================================

// Helper function needed by new algorithms
function detectStreakAndBreak(history_str) {
    if (history_str.length === 0) {
        return { streak: 0, currentResult: null, breakProb: 0.5 };
    }
    const currentResult = history_str[0];
    let streak = 0;
    for (const res of history_str) {
        if (res === currentResult) {
            streak++;
        } else {
            break;
        }
    }
    // Simple break probability model: increases with streak length
    const breakProb = Math.min(0.95, 0.5 + (streak - 3) * 0.1);
    return { streak, currentResult, breakProb };
}

// 1. Định nghĩa các Patterns
function define_patterns() {
    const patterns = {
        // --- Cầu Bệt (Streaks) ---
        "Bệt": h => h.length >= 3 && h[0] === h[1] && h[1] === h[2],
        "Bệt siêu dài": h => h.length >= 5 && h.slice(0, 5).every(x => x === h[0]),
        "Bệt gãy nhẹ": h => h.length >= 4 && h[0] !== h[1] && h[1] === h[2] && h[2] === h[3],
        "Bệt gãy sâu": h => h.length >= 5 && h[0] !== h[1] && h.slice(1, 5).every(x => x === h[1]),
        "Bệt xen kẽ ngắn": h => h.length >= 4 && h[3] === h[2] && h[1] === h[0] && h[3] !== h[1],
        "Bệt ngược": h => h.length >= 4 && h[0] === h[1] && h[2] === h[3] && h[0] !== h[2],
        "Xỉu kép": h => h.length >= 2 && h[0] === 'Xỉu' && h[1] === 'Xỉu',
        "Tài kép": h => h.length >= 2 && h[0] === 'Tài' && h[1] === 'Tài',
        "Ngẫu nhiên bệt": h => h.length > 8 && (h.slice(0, 8).filter(x=>x==='Tài').length/8) > 0.4 && (h.slice(0, 8).filter(x=>x==='Tài').length/8) < 0.6 && h[0] === h[1],
        // --- Cầu Đảo (Alternating) ---
        "Đảo 1-1": h => h.length >= 4 && h[0] !== h[1] && h[1] !== h[2] && h[2] !== h[3],
        "Xen kẽ dài": h => h.length >= 5 && h[0]!==h[1] && h[1]!==h[2] && h[2]!==h[3] && h[3]!==h[4],
        "Xen kẽ": h => h.length >= 3 && h[0] !== h[1] && h[1] !== h[2],
        "Xỉu lắc": h => h.length >= 4 && h.slice(0,4).join(',') === ['Tài', 'Xỉu', 'Tài', 'Xỉu'].reverse().join(','),
        "Tài lắc": h => h.length >= 4 && h.slice(0,4).join(',') === ['Xỉu', 'Tài', 'Xỉu', 'Tài'].reverse().join(','),
        // --- Cầu theo nhịp (Rhythmic) ---
        "Kép 2-2": h => h.length >= 4 && h[0]===h[1] && h[2]===h[3] && h[0]!==h[2],
        "Nhịp 3-3": h => h.length >= 6 && h.slice(0,3).every(x=>x===h[0]) && h.slice(3,6).every(x=>x===h[3]),
        "Nhịp 4-4": h => h.length >= 8 && h.slice(0,4).every(x=>x===h[0]) && h.slice(4,8).every(x=>x===h[4]) && h[0] !== h[4],
        "Lặp 2-1": h => h.length >= 3 && h[1]===h[2] && h[0]!==h[1],
        "Lặp 3-2": h => h.length >= 5 && h.slice(2,5).every(x=>x===h[2]) && h[0]===h[1] && h[2]!==h[0],
        "Cầu 3-1": h => h.length >= 4 && h.slice(1,4).every(x=>x===h[1]) && h[0]!==h[1],
        "Cầu 4-1": h => h.length >= 5 && h.slice(1,5).every(x=>x===h[1]) && h[0]!==h[1],
        "Cầu 1-2-1": h => h.length >= 4 && h[0] !== h[1] && h[1] === h[2] && h[2] !== h[3] && h[0] === h[3],
        "Cầu 2-1-2": h => h.length >= 5 && h[0]===h[1] && h[3]===h[4] && h[2]!==h[1] && h[0]===h[4],
        "Cầu 3-1-2": h => h.length >= 6 && h.slice(3,6).every(x=>x===h[3]) && h[1]===h[2] && h[3]!==h[1] && new Set(h.slice(0,6)).size === 2,
        "Cầu 1-2-3": h => h.length >= 6 && h[0]===h[1]===h[2] && h[3]===h[4] && h[3]!==h[0] && new Set(h.slice(0,6)).size === 2,
        "Dài ngắn đảo": h => h.length >= 5 && h.slice(2,5).every(x=>x===h[2]) && h[0]!==h[1] && h[0]!==h[2],
        // --- Cầu Chu Kỳ & Đối Xứng (Cyclic & Symmetric) ---
        "Chu kỳ 2": h => h.length >= 4 && h[0] === h[2] && h[1] === h[3],
        "Chu kỳ 3": h => h.length >= 6 && h[0] === h[3] && h[1] === h[4] && h[2] === h[5],
        "Chu kỳ 4": h => h.length >= 8 && h.slice(0,4).join('') === h.slice(4,8).join(''),
        "Đối xứng (Gương)": h => h.length >= 5 && h[0] === h[4] && h[1] === h[3],
        "Bán đối xứng": h => h.length >= 5 && h[0] === h[3] && h[1] === h[4],
        "Ngược chu kỳ": h => h.length >= 4 && h[0] === h[3] && h[1] === h[2] && h[0] !== h[1],
        "Chu kỳ biến đổi": h => h.length >= 5 && h[0]===h[2]===h[4] && h[1]===h[3],
        "Cầu linh hoạt": h => h.length >= 6 && h[0]===h[2]===h[4] && h[1]===h[3]===h[5],
        "Chu kỳ tăng": h => h.length >= 6 && h[0]===h[2]===h[4] && h[1]===h[3]===h[5] && h[0] !== h[1],
        "Chu kỳ giảm": h => h.length >= 6 && h[0]===h[1] && h[2]===h[3] && h[4]===h[5] && new Set(h.slice(0,6)).size === 3,
        "Cầu lặp": h => h.length >= 6 && h.slice(0,3).join('') === h.slice(3,6).join(''),
        "Gãy ngang": h => h.length >= 4 && h[0] === h[2] && h[1] === h[3] && h[0] !== h[1],
        // --- Cầu Phức Tạp & Tổng Hợp ---
        "Gập ghềnh": h => h.length >= 5 && h[0] === h[4] && h[1]===h[2] && h[0]===h[3],
        "Bậc thang": h => h.length >= 3 && h[1] === h[2] && h[0] !== h[1],
        "Cầu đôi": h => h.length >= 4 && h[0] === h[1] && h[2] !== h[3] && h[2] !== h[0],
        "Đối ngược": h => h.length >= 4 && h[0] === (h[1]==='Tài'?'Xỉu':'Tài') && h[2] === (h[3]==='Tài'?'Xỉu':'Tài'),
        "Cầu gập": h => h.length >= 5 && h[1]===h[2] && h[3]===h[4] && h[0]!==h[1] && h[1]!==h[3],
        "Phối hợp 1": h => h.length >= 5 && h[0] === h[1] && h[2] !== h[3],
        "Phối hợp 2": h => h.length >= 4 && h.slice(0,4).join(',') === ['Tài','Xỉu','Tài','Tài'].reverse().join(','),
        "Phối hợp 3": h => h.length >= 4 && h.slice(0,4).join(',') === ['Xỉu','Tài','Xỉu','Xỉu'].reverse().join(','),
        "Chẵn lẻ lặp": h => h.length >= 4 && h[2]===h[3] && h[0]===h[1] && h[0] !== h[2],
        "Cầu dài ngẫu": h => h.length >= 7 && h.slice(3,7).every(x=>x===h[3]) && new Set(h.slice(0,3)).size > 1,
        // --- Cầu Dựa Trên Phân Bố (Statistical) ---
        "Ngẫu nhiên": h => h.length > 10 && (h.slice(0,10).filter(x=>x==='Tài').length/10) > 0.4 && (h.slice(0,10).filter(x=>x==='Tài').length/10) < 0.6,
        "Đa dạng": h => h.length >= 5 && new Set(h.slice(0,5)).size === 2,
        "Phân cụm": h => h.length >= 6 && (h.slice(3,6).every(x=>x==='Tài') || h.slice(3,6).every(x=>x==='Xỉu')),
        "Lệch ngẫu nhiên": h => h.length > 10 && ((h.slice(0,10).filter(x=>x==='Tài').length/10) > 0.7 || (h.slice(0,10).filter(x=>x==='Xỉu').length/10) > 0.7),
        // --- Siêu Cầu (Super Patterns) ---
        "Cầu Tiến 1-1-2-2": h => h.length >= 6 && h[4]!==h[5] && h[2]===h[3] && h[0]===h[1] && new Set(h.slice(0,6)).size === 2,
        "Cầu Lùi 3-2-1": h => h.length >= 6 && h.slice(3,6).every(x=>x===h[3]) && h[1]===h[2] && h[0]!==h[1] && new Set(h.slice(0,6)).size === 2,
        "Cầu Sandwich": h => h.length >= 5 && h[0] === h[4] && h.slice(1,4).every(x=>x===h[1]) && h[0] !== h[1],
        "Cầu Thang máy": h => h.length >= 7 && ['T', 'T', 'X', 'X', 'T', 'T', 'X'].reverse().join('') === h.slice(0,7).map(x=>x[0]).join('') || ['X', 'X', 'T', 'T', 'X', 'X', 'T'].reverse().join('') === h.slice(0,7).map(x=>x[0]).join(''),
        "Cầu Sóng vỗ": h => h.length >= 8 && h[0]===h[1] && h[3]===h[4] && h[6]===h[7] && h[2]===h[5] && h[0]!==h[2],
    };
    return patterns;
}

// 2. Các hàm cập nhật và huấn luyện mô hình
function update_transition_matrix(prev_result, current_result) {
    if (!prev_result) return;
    const prev_idx = prev_result === 'Tài' ? 0 : 1;
    const curr_idx = current_result === 'Tài' ? 0 : 1;
    transition_counts[prev_idx][curr_idx] += 1;
    
    for (let i = 0; i < 2; i++) {
        const total_transitions = transition_counts[i][0] + transition_counts[i][1];
        const alpha = 1; // Laplace smoothing
        const num_outcomes = 2;
        if (total_transitions > 0) {
            transition_matrix[i][0] = (transition_counts[i][0] + alpha) / (total_transitions + alpha * num_outcomes);
            transition_matrix[i][1] = (transition_counts[i][1] + alpha) / (total_transitions + alpha * num_outcomes);
        }
    }
}

function update_pattern_accuracy(predicted_pattern_name, prediction, actual_result) {
    if (!predicted_pattern_name) return;
    if (!pattern_accuracy.has(predicted_pattern_name)) {
        pattern_accuracy.set(predicted_pattern_name, { success: 0, total: 0 });
    }
    const stats = pattern_accuracy.get(predicted_pattern_name);
    stats.total += 1;
    if (prediction === actual_result) {
        stats.success += 1;
    }
}

function get_logistic_features(history_str) {
    if (!history_str || history_str.length === 0) return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0];

    // Feature 1: Current streak length
    let current_streak = 0;
    if (history_str.length > 0) {
        const last = history_str[0];
        current_streak = 1;
        for (let i = 1; i < history_str.length; i++) {
            if (history_str[i] === last) current_streak++;
            else break;
        }
    }

    // Feature 2: Previous streak length
    let previous_streak_len = 0;
    if (history_str.length > current_streak) {
        const prev_streak_start_idx = current_streak;
        const prev_streak_val = history_str[prev_streak_start_idx];
        previous_streak_len = 1;
        for (let i = prev_streak_start_idx + 1; i < history_str.length; i++) {
            if (history_str[i] === prev_streak_val) previous_streak_len++;
            else break;
        }
    }

    // Feature 3 & 4: Balance (Tài-Xỉu) short-term and long-term
    const recent_history = history_str.slice(0, 20);
    const balance_short = (recent_history.filter(x => x === 'Tài').length - recent_history.filter(x => x === 'Xỉu').length) / Math.max(1, recent_history.length);
    
    const long_history = history_str.slice(0, 100);
    const balance_long = (long_history.filter(x => x === 'Tài').length - long_history.filter(x => x === 'Xỉu').length) / Math.max(1, long_history.length);

    // Feature 5: Volatility
    let changes = 0;
    for (let i = 0; i < recent_history.length - 1; i++) {
        if (recent_history[i] !== recent_history[i+1]) changes++;
    }
    const volatility = recent_history.length > 1 ? changes / (recent_history.length - 1) : 0.0;
    
    // Feature 6: Alternation count in last 10 results
    const last_10 = history_str.slice(0, 10);
    let alternations = 0;
    for (let i = 0; i < last_10.length - 1; i++) {
        if (last_10[i] !== last_10[i+1]) alternations++;
    }

    return [current_streak, previous_streak_len, balance_short, balance_long, volatility, alternations].map(f => parseFloat(f));
}

function train_logistic_regression(features, actual_result) {
    const y = actual_result === 'Tài' ? 1.0 : 0.0;
    const z = logistic_bias + features.reduce((sum, f, i) => sum + logistic_weights[i] * f, 0);
    
    let p;
    if (-z > 700) p = 0.0;
    else if (-z < -700) p = 1.0;
    else p = 1.0 / (1.0 + Math.exp(-z));
        
    const error = y - p;
    logistic_bias += learning_rate * error;
    for (let i = 0; i < logistic_weights.length; i++) {
        const gradient = error * features[i];
        const regularization_term = regularization * logistic_weights[i];
        logistic_weights[i] += learning_rate * (gradient - regularization_term);
    }
}

function update_model_weights() {
    let total_accuracy_score = 0;
    const accuracies_raw = {};
    
    for (const name in model_performance) {
        const perf = model_performance[name];
        if (perf.total > 5) {
            const accuracy = perf.success / perf.total;
            accuracies_raw[name] = accuracy;
            total_accuracy_score += accuracy;
        } else {
            accuracies_raw[name] = default_model_weights[name] * 2; // Ưu tiên khởi tạo
            total_accuracy_score += accuracies_raw[name];
        }
    }

    if (total_accuracy_score > 0) {
        for (const name in model_weights) {
            model_weights[name] = (accuracies_raw[name] || 0) / total_accuracy_score;
        }
    } else {
        model_weights = { ...default_model_weights };
    }
        
    const sum_weights = Object.values(model_weights).reduce((a, b) => a + b, 0);
    if (sum_weights > 0) {
        for (const name in model_weights) {
            model_weights[name] /= sum_weights;
        }
    }
}

// 3. Các hàm dự đoán cốt lõi
function detect_pattern(history_str) {
    if (history_str.length < 2) return null;
    
    const detected_patterns = [];
    let total_occurrences = 0;
    pattern_accuracy.forEach(s => total_occurrences += s.total);
    total_occurrences = Math.max(1, total_occurrences);

    for (const name in patterns) {
        try {
            if (patterns[name](history_str)) {
                const stats = pattern_accuracy.get(name) || { success: 0, total: 0 };
                const accuracy = (stats.total > 10) ? (stats.success / stats.total) : 0.55;
                const recency_score = stats.total / total_occurrences;
                const weight = 0.7 * accuracy + 0.3 * recency_score;
                detected_patterns.push({ name, weight });
            }
        } catch (e) { continue; }
    }

    if (detected_patterns.length === 0) return null;
    return detected_patterns.reduce((max, p) => p.weight > max.weight ? p : max, detected_patterns[0]);
}

function predict_with_pattern(history_str, detected_pattern_info) {
    if (!detected_pattern_info || history_str.length < 2) {
        return { prediction: 'Tài', confidence: 0.5 };
    }

    const name = detected_pattern_info.name;
    const last = history_str[0];
    const prev = history_str[1];
    const anti_last = last === 'Tài' ? 'Xỉu' : 'Tài';

    let prediction;

    if (["Bệt", "kép", "2-2", "3-3", "4-4", "Nhịp", "Sóng vỗ", "Cầu 3-1", "Cầu 4-1", "Lặp"].some(p => name.includes(p))) {
        prediction = last; // Theo cầu
    } else if (["Đảo 1-1", "Xen kẽ", "lắc", "Đối ngược", "gãy", "Bậc thang", "Dài ngắn đảo"].some(p => name.includes(p))) {
        prediction = anti_last; // Bẻ cầu
    } else if (["Chu kỳ 2", "Gãy ngang", "Chu kỳ tăng", "Chu kỳ giảm"].some(p => name.includes(p))) {
        prediction = prev;
    } else if (name.includes('Chu kỳ 3')) {
        prediction = history_str[2];
    } else if (name.includes('Chu kỳ 4')) {
        prediction = history_str[3];
    } else if (name === "Cầu 2-1-2") {
        prediction = history_str[4];
    } else if (name === "Cầu 1-2-1") {
        prediction = anti_last;
    } else if (name === "Đối xứng (Gương)") {
        prediction = history_str[2];
    } else if (name === "Cầu lặp") {
        prediction = history_str[2];
    } else if (name === "Cầu Sandwich") {
        prediction = anti_last;
    } else if (name === "Cầu Thang máy") {
        prediction = history_str[2];
    } else {
        prediction = anti_last; // Mặc định bẻ cầu
    }
        
    return { prediction, confidence: detected_pattern_info.weight };
}

// --- NEW ALGORITHMS ---
function trendAndProb(history_str) {
  const { streak, currentResult, breakProb } = detectStreakAndBreak(history_str);
  if (streak >= 5) {
    if (breakProb > 0.7) {
      return currentResult === 'Tài' ? 2 : 1; // 2: Xỉu, 1: Tài
    }
    return currentResult === 'Tài' ? 1 : 2;
  }
  const last15 = history_str.slice(0, 15).reverse();
  if (!last15.length) return 0;
  const weights = last15.map((_, i) => Math.pow(1.3, i));
  const taiWeighted = weights.reduce((sum, w, i) => sum + (last15[i] === 'Tài' ? w : 0), 0);
  const xiuWeighted = weights.reduce((sum, w, i) => sum + (last15[i] === 'Xỉu' ? w : 0), 0);
  const totalWeight = taiWeighted + xiuWeighted;
  const last10 = last15.slice(-10);
  const patterns = [];
  if (last10.length >= 4) {
    for (let i = 0; i <= last10.length - 4; i++) {
      patterns.push(last10.slice(i, i + 4).join(','));
    }
  }
  const patternCounts = patterns.reduce((acc, p) => { acc[p] = (acc[p] || 0) + 1; return acc; }, {});
  const mostCommon = Object.entries(patternCounts).sort((a, b) => b[1] - a[1])[0];
  if (mostCommon && mostCommon[1] >= 3) {
    const pattern = mostCommon[0].split(',');
    return pattern[pattern.length - 1] !== last10[last10.length - 1] ? 1 : 2;
  } else if (totalWeight > 0 && Math.abs(taiWeighted - xiuWeighted) / totalWeight >= 0.2) {
    return taiWeighted > xiuWeighted ? 1 : 2;
  }
  return last15[last15.length - 1] === 'Xỉu' ? 1 : 2;
}

function shortPattern(history_str) {
  const { streak, currentResult, breakProb } = detectStreakAndBreak(history_str);
  if (streak >= 4) {
    if (breakProb > 0.7) {
      return currentResult === 'Tài' ? 2 : 1;
    }
    return currentResult === 'Tài' ? 1 : 2;
  }
  const last8 = history_str.slice(0, 8).reverse();
  if (!last8.length) return 0;
  const patterns = [];
  if (last8.length >= 3) {
    for (let i = 0; i <= last8.length - 3; i++) {
      patterns.push(last8.slice(i, i + 3).join(','));
    }
  }
  const patternCounts = patterns.reduce((acc, p) => { acc[p] = (acc[p] || 0) + 1; return acc; }, {});
  const mostCommon = Object.entries(patternCounts).sort((a, b) => b[1] - a[1])[0];
  if (mostCommon && mostCommon[1] >= 2) {
    const pattern = mostCommon[0].split(',');
    return pattern[pattern.length - 1] !== last8[last8.length - 1] ? 1 : 2;
  }
  return last8[last8.length - 1] === 'Xỉu' ? 1 : 2;
}

function meanDeviation(history_str) {
  const { streak, currentResult, breakProb } = detectStreakAndBreak(history_str);
  if (streak >= 4) {
    if (breakProb > 0.7) {
      return currentResult === 'Tài' ? 2 : 1;
    }
    return currentResult === 'Tài' ? 1 : 2;
  }
  const last12 = history_str.slice(0, 12);
  if (!last12.length) return 0;
  const taiCount = last12.filter(r => r === 'Tài').length;
  const xiuCount = last12.length - taiCount;
  const deviation = Math.abs(taiCount - xiuCount) / last12.length;
  if (deviation < 0.3) {
    return last12[0] === 'Xỉu' ? 1 : 2; // last12[0] is the newest
  }
  return xiuCount > taiCount ? 1 : 2;
}

function recentSwitch(history_str) {
  const { streak, currentResult, breakProb } = detectStreakAndBreak(history_str);
  if (streak >= 4) {
    if (breakProb > 0.7) {
      return currentResult === 'Tài' ? 2 : 1;
    }
    return currentResult === 'Tài' ? 1 : 2;
  }
  const last10 = history_str.slice(0, 10);
  if (!last10.length) return 0;
  const switches = last10.slice(0, -1).reduce((count, curr, idx) => count + (curr !== last10[idx + 1] ? 1 : 0), 0);
  return switches >= 5 ? (last10[0] === 'Xỉu' ? 1 : 2) : (last10[0] === 'Xỉu' ? 1 : 2);
}

// --- END OF NEW ALGORITHMS ---

function apply_meta_logic(prediction, confidence, history_str) {
    let final_prediction = prediction;
    let final_confidence = confidence;
    let reason = "";

    const { streak, currentResult } = detectStreakAndBreak(history_str);
    
    if (streak >= 9 && prediction === currentResult) {
        final_prediction = currentResult === 'Tài' ? 'Xỉu' : 'Tài';
        final_confidence = 78.0;
        reason = `Bẻ cầu bệt siêu dài (${streak})`;
    } else if (streak >= 7 && prediction === currentResult) {
        final_confidence = Math.max(50.0, confidence - 15);
        reason = `Cầu bệt dài (${streak}), giảm độ tin cậy`;
    }
        
    return { final_prediction, final_confidence, reason };
}

function predict_advanced() {
    if (history.length < MIN_HISTORY_FOR_PREDICTION) {
        return {
            prediction: "Đang tích dữ liệu",
            reason: `Lịch sử: ${history.length}/${MIN_HISTORY_FOR_PREDICTION}`,
            confidence: 0,
            individual_predictions: null,
            features: null,
            next_session_id: (rikCurrentSession || 0) + 1,
        };
    }

    const last_result = history[0];
    const numToResult = (num) => (num === 1 ? 'Tài' : (num === 2 ? 'Xỉu' : null));

    // --- Model 1: Pattern Matching ---
    const detected_pattern_info = detect_pattern(history);
    const { prediction: patt_pred, confidence: patt_conf } = predict_with_pattern(history, detected_pattern_info);

    // --- Model 2: Markov Chain ---
    const last_result_idx = last_result === 'Tài' ? 0 : 1;
    const prob_tai_markov = transition_matrix[last_result_idx][0];
    const markov_pred = prob_tai_markov >= 0.5 ? 'Tài' : 'Xỉu';
    const markov_conf_scaled = Math.max(prob_tai_markov, 1 - prob_tai_markov);

    // --- Model 3: Logistic Regression ---
    const features = get_logistic_features(history);
    const z = logistic_bias + features.reduce((sum, f, i) => sum + logistic_weights[i] * f, 0);
    let prob_tai_logistic;
    if (-z > 700) prob_tai_logistic = 0.0; else if (-z < -700) prob_tai_logistic = 1.0; else prob_tai_logistic = 1.0 / (1.0 + Math.exp(-z));
    const logistic_pred = prob_tai_logistic >= 0.5 ? 'Tài' : 'Xỉu';
    const logistic_conf_scaled = Math.max(prob_tai_logistic, 1 - prob_tai_logistic);
    
    // --- New Models ---
    const trend_pred = numToResult(trendAndProb(history));
    const short_pred = numToResult(shortPattern(history));
    const mean_pred = numToResult(meanDeviation(history));
    const switch_pred = numToResult(recentSwitch(history));

    const individual_predictions = {
        pattern: patt_pred,
        markov: markov_pred,
        logistic: logistic_pred,
        trend: trend_pred,
        short: short_pred,
        mean: mean_pred,
        switch: switch_pred,
    };

    // --- Ensemble Prediction ---
    const predictions_with_weights = {
        pattern: { pred: patt_pred, conf: patt_conf, weight: model_weights.pattern },
        markov: { pred: markov_pred, conf: markov_conf_scaled, weight: model_weights.markov },
        logistic: { pred: logistic_pred, conf: logistic_conf_scaled, weight: model_weights.logistic },
        trend: { pred: trend_pred, conf: 0.6, weight: model_weights.trend },
        short: { pred: short_pred, conf: 0.6, weight: model_weights.short },
        mean: { pred: mean_pred, conf: 0.6, weight: model_weights.mean },
        switch: { pred: switch_pred, conf: 0.6, weight: model_weights.switch },
    };
    
    let tai_score = 0.0, xiu_score = 0.0;
    for (const modelName in predictions_with_weights) {
        const model_info = predictions_with_weights[modelName];
        if (!model_info.pred) continue; // Skip if a model fails to predict
        const score = model_info.conf * model_info.weight;
        if (model_info.pred === 'Tài') tai_score += score;
        else xiu_score += score;
    }

    let final_prediction = tai_score > xiu_score ? 'Tài' : 'Xỉu';
    const total_score = tai_score + xiu_score;
    let final_confidence = (total_score > 0) ? (Math.max(tai_score, xiu_score) / total_score * 100) : 50.0;
    
    if (detected_pattern_info && detected_pattern_info.weight > 0.6 && patt_pred === final_prediction) {
        final_confidence = Math.min(98.0, final_confidence + (patt_conf * 10));
    }

    // --- Meta Logic ---
    const meta = apply_meta_logic(final_prediction, final_confidence, history);
    final_prediction = meta.final_prediction;
    final_confidence = meta.final_confidence;
    
    let reason = detected_pattern_info ? detected_pattern_info.name : "Ensemble";
    if (meta.reason) {
        reason = meta.reason;
    }
    
    return {
        prediction: final_prediction,
        reason: reason,
        confidence: parseFloat(final_confidence.toFixed(2)),
        individual_predictions,
        features,
        next_session_id: (rikCurrentSession || 0) + 1,
    };
}


// =================================================================
// --- WEB SOCKET & DATA PROCESSING ---
// =================================================================

function connectRikWebSocket() {
  console.log("🔌 Connecting to SunWin WebSocket...");
  rikWS = new WebSocket(`wss://websocket.azhkthg1.net/websocket?token=${TOKEN}`);

  rikWS.on("open", () => {
    const authPayload = [1,"MiniGame","SC_nguyenvantinhne","tinhbip",{"info": "{\"ipAddress\":\"2001:ee0:514e:1a90:d1dd:67c5:a601:2e90\",\"wsToken\":\"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhbW91bnQiOjAsImdlbmRlciI6MCwiZGlzcGxheU5hbWUiOiJzdW53aW50aGFjaG9lbTEiLCJwaG9uZVZlcmlmaWVkIjpmYWxzZSwiYm90IjowLCJhdmF0YXIiOiJodHRwczovL2ltYWdlcy5zd2luc2hvcC5uZXQvaW1hZ2VzL2F2YXRhci9hdmF0YXJfMTEucG5nIiwidXNlcklkIjoiY2IwYWE5ZmEtZjI0OS00NjA0LWIzNTUtZTAyMDhiMTkyMDljIiwicmVnVGltZSI6MTY5NzAyNDMyMjgyMSwicGhvbmUiOiIiLCJjdXN0b21lcklkIjoxMzAwNTU5MDAsImJyYW5kIjoic3VuLndpbiIsInVzZXJuYW1lIjoiU0Nfbmd1eWVudmFudGluaG5lIiwidGltZXN0YW1wIjoxNzUyODM0MDU5NjE4fQ.Q-d60oNt6RIjw-orYsz8aTYB__3HLLuhSbQw-XVGuAA\",\"userId\":\"cb0aa9fa-f249-4604-b355-e0208b19209c\",\"username\":\"SC_nguyenvantinhne\",\"timestamp\":1752834059619}","signature": "2DD52993E712B038F47FAEDEE21EA1EB9CC880317280AD713ECFBD2CB67BB25AC2E3B9256799A8FC900D8CDB27FCA2BD595FCA9D3433647C8E6DA4996FE7410513A78F6455DF603B0958D76B228BF94F30C014157B2C8233135C7870254A8EE71B65F6CB948E47710EA0953B74F0C46D889F814F1C24404F5660CC9357A6C859","pid": 5,"subi": true}];
    rikWS.send(JSON.stringify(authPayload));
    clearInterval(rikIntervalCmd);
    rikIntervalCmd = setInterval(sendRikCmd1005, 5000);
  });

  rikWS.on("message", (data) => {
    try {
      const json = typeof data === 'string' ? JSON.parse(data) : decodeBinaryMessage(data);
      if (!json) return;

      // Nhận kết quả phiên mới
      if (Array.isArray(json) && json[3]?.res?.d1 && json[3]?.res?.sid) {
        const result = json[3].res;
        
        if (!rikCurrentSession || result.sid > rikCurrentSession) {
          const wasCollecting = history.length < MIN_HISTORY_FOR_PREDICTION;
          rikCurrentSession = result.sid;
          const actualResultStr = getKetQua(result.d1, result.d2, result.d3);

          // 1. --- LEARNING STEP --- (Only learn if we were already predicting)
          if (last_prediction && last_prediction.individual_predictions) {
              const predResult = last_prediction.prediction === actualResultStr;
              overall_performance.total++;
              if(predResult) overall_performance.success++;
              
              for (const modelName in last_prediction.individual_predictions) {
                  model_performance[modelName].total++;
                  if (last_prediction.individual_predictions[modelName] === actualResultStr) {
                      model_performance[modelName].success++;
                  }
              }

              update_transition_matrix(history[0] || null, actualResultStr);
              if(last_prediction.features) {
                train_logistic_regression(last_prediction.features, actualResultStr);
              }
              update_pattern_accuracy(last_prediction.reason, last_prediction.prediction, actualResultStr);
              update_model_weights();
          }

          // 2. --- UPDATE HISTORY ---
          rikResults.unshift({ sid: result.sid, d1: result.d1, d2: result.d2, d3: result.d3 });
          if (rikResults.length > MAX_HISTORY_LEN) rikResults.pop();
          
          history.unshift(actualResultStr);
          if (history.length > MAX_HISTORY_LEN) history.pop();

          console.log(`📥 Phiên mới ${result.sid} → ${actualResultStr} (${getTX(result.d1, result.d2, result.d3)})`);
          
          if (wasCollecting && history.length >= MIN_HISTORY_FOR_PREDICTION) {
            console.log(`✅ Đã thu thập đủ ${MIN_HISTORY_FOR_PREDICTION} phiên. Bắt đầu dự đoán thực tế.`);
          }

          // 3. --- PREDICTION STEP for the NEXT round ---
          last_prediction = predict_advanced();
          if(last_prediction.confidence > 0) {
            console.log(`🔮 Dự đoán phiên ${last_prediction.next_session_id}: ${last_prediction.prediction} (${last_prediction.confidence}%) - Lý do: ${last_prediction.reason}`);
          } else {
            console.log(`⏳ ${last_prediction.reason}`);
          }
          
          setTimeout(() => {
            if (rikWS) rikWS.close();
          }, 1000);
        }
      }
      // Nhận lịch sử ban đầu
      else if (Array.isArray(json) && json[1]?.htr) {
        const historyData = json[1].htr.map((item) => ({sid: item.sid, d1: item.d1, d2: item.d2, d3: item.d3,})).sort((a, b) => b.sid - a.sid);

        rikResults = historyData.slice(0, MAX_HISTORY_LEN);
        history = rikResults.map(item => getKetQua(item.d1, item.d2, item.d3));
        rikCurrentSession = rikResults.length > 0 ? rikResults[0].sid : null;

        console.log(`📦 Đã tải ${history.length} phiên lịch sử.`);

        if (history.length >= MIN_HISTORY_FOR_PREDICTION) {
            console.log("Bắt đầu quá trình học với dữ liệu lịch sử...");
            for (let i = history.length - 2; i >= 0; i--) {
                const current = history[i];
                const prev = history[i+1];
                update_transition_matrix(prev, current);
                const features = get_logistic_features(history.slice(i + 1));
                train_logistic_regression(features, current);
            }
            console.log("🤖 Đã huấn luyện xong. Bắt đầu dự đoán...");
        }

        last_prediction = predict_advanced(); // Dự đoán lần đầu
        if(last_prediction.confidence > 0) {
            console.log(`🔮 Dự đoán phiên ${last_prediction.next_session_id}: ${last_prediction.prediction} (${last_prediction.confidence}%) - Lý do: ${last_prediction.reason}`);
        } else {
            console.log(`⏳ ${last_prediction.reason}`);
        }
      }
    } catch (e) {
      console.error("❌ Parse error:", e.message, e.stack);
    }
  });

  rikWS.on("close", () => {
    console.log("🔌 WebSocket disconnected. Reconnecting in 5s...");
    clearInterval(rikIntervalCmd);
    setTimeout(connectRikWebSocket, 5000);
  });

  rikWS.on("error", (err) => {
    console.error("🔌 WebSocket error:", err.message);
    if(rikWS) rikWS.close();
  });
}

// =================================================================
// --- API SERVER ---
// =================================================================

fastify.register(cors);

fastify.get("/api/taixiu/sunwin", async () => {
  const validResults = rikResults.filter(item => item.d1 && item.d2 && item.d3);
  if (validResults.length === 0) {
    return { message: "Không có dữ liệu lịch sử." };
  }
  const current = validResults[0];
  const sum = current.d1 + current.d2 + current.d3;
  return {
    phien: current.sid,
    xuc_xac_1: current.d1,
    xuc_xac_2: current.d2,
    xuc_xac_3: current.d3,
    tong: sum,
    ket_qua: getKetQua(current.d1, current.d2, current.d3)
  };
});

fastify.get("/api/taixiu/predict", async () => {
    if (!last_prediction) {
        return { message: "Đang khởi tạo thuật toán, vui lòng chờ..." };
    }
    
    // Xử lý trường hợp đang tích lũy dữ liệu
    if (last_prediction.confidence === 0) {
         return {
            du_doan_phien: last_prediction.next_session_id,
            ket_qua_du_doan: "Chờ",
            do_tin_cay: 0,
            phuong_phap: last_prediction.reason
        };
    }

    return {
        du_doan_phien: last_prediction.next_session_id,
        ket_qua_du_doan: last_prediction.prediction,
        do_tin_cay: last_prediction.confidence,
        phuong_phap: last_prediction.reason
    };
});

fastify.get("/api/taixiu/performance", async () => {
    const patternPerf = {};
    pattern_accuracy.forEach((value, key) => {
        patternPerf[key] = {
            ...value,
            accuracy: value.total > 0 ? parseFloat(((value.success / value.total) * 100).toFixed(2)) : 0
        };
    });

    const modelPerfFormatted = {};
    for (const modelName in model_performance) {
        const perf = model_performance[modelName];
        modelPerfFormatted[modelName] = {
            ...perf,
            accuracy: perf.total > 0 ? parseFloat(((perf.success / perf.total) * 100).toFixed(2)) : 0,
        };
    }

    return {
        hieu_suat_tong_the: {
            ...overall_performance,
            accuracy: overall_performance.total > 0 ? parseFloat(((overall_performance.success / overall_performance.total) * 100).toFixed(2)) : 0
        },
        trong_so_mo_hinh_hien_tai: model_weights,
        hieu_suat_tung_mo_hinh: modelPerfFormatted,
        trang_thai_hoc: {
          ma_tran_markov: transition_matrix,
          trong_so_logistic: logistic_weights,
          bias_logistic: logistic_bias
        },
        hieu_suat_chi_tiet_pattern: patternPerf,
    };
});


const start = async () => {
  try {
    connectRikWebSocket();
    const address = await fastify.listen({ port: PORT, host: "0.0.0.0" });
    console.log(`🚀 API chạy tại ${address}`);
  } catch (err) {
    console.error("❌ Server error:", err);
    process.exit(1);
  }
};

start();