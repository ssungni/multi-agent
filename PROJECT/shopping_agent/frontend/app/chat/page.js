"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, clearToken, getToken } from "../../lib/api";

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [pendingProducts, setPendingProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    loadCart();
  }, []);

  async function loadCart() {
    try {
      const items = await apiFetch("/cart");
      setCart(items);
    } catch (err) {
      // 로그인 만료 등 - 채팅 자체는 계속 시도해볼 수 있으니 조용히 무시
    }
  }

  async function sendMessage(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setError("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setSending(true);

    try {
      const data = await apiFetch("/agent/chat", {
        method: "POST",
        body: JSON.stringify({ message: text, thread_id: threadId }),
      });
      setThreadId(data.thread_id);
      setMessages((m) => [...m, { role: "assistant", content: data.message }]);
      setPendingProducts(data.awaiting_confirmation ? data.products : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  async function confirmAdd(productId, confirm) {
    setError("");
    try {
      const data = await apiFetch("/agent/chat/confirm", {
        method: "POST",
        body: JSON.stringify({ thread_id: threadId, product_id: productId, confirm }),
      });
      setMessages((m) => [
        ...m,
        { role: "assistant", content: confirm ? "장바구니에 담았어요." : "담지 않았어요." },
      ]);
      setPendingProducts([]);
      if (data.added_product_id) loadCart();
    } catch (err) {
      setError(err.message);
    }
  }

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <div className="chat-layout">
      <div className="chat-main">
        <div style={{ padding: 12, borderBottom: "1px solid #eee", display: "flex", justifyContent: "space-between" }}>
          <strong>CartMate</strong>
          <button onClick={logout}>로그아웃</button>
        </div>

        <div className="messages">
          {messages.length === 0 && (
            <p style={{ color: "#888", fontSize: 13 }}>
              예: "여름에 신을 운동화 추천해줘", "5만원 이하 화장품 있어?"
            </p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.content}
            </div>
          ))}

          {pendingProducts.length > 0 && (
            <div>
              {pendingProducts.map((p) => (
                <div key={p.id} className="product-card">
                  <span>
                    {p.name} · {p.brand} · {p.price.toLocaleString()}원
                  </span>
                  <div style={{ display: "flex", gap: 6 }}>
                    <button onClick={() => confirmAdd(p.id, true)}>담기</button>
                    <button onClick={() => confirmAdd(p.id, false)}>취소</button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {error && <p className="error">{error}</p>}
        </div>

        <form className="chat-input" onSubmit={sendMessage}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="메시지를 입력하세요"
            disabled={sending}
          />
          <button type="submit" disabled={sending}>
            {sending ? "전송 중..." : "전송"}
          </button>
        </form>
      </div>

      <div className="cart-panel">
        <h3>장바구니</h3>
        {cart.length === 0 && <p style={{ fontSize: 13, color: "#888" }}>비어있음</p>}
        {cart.map((item) => (
          <div key={item.id} className="cart-item">
            {item.product.name} x{item.quantity}
            <br />
            {item.product.price.toLocaleString()}원
          </div>
        ))}
        <button style={{ marginTop: 8 }} onClick={loadCart}>
          새로고침
        </button>
      </div>
    </div>
  );
}
