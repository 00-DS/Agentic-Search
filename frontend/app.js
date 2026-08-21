


// 这是教学示例，展示组织方式
const API = "http://localhost:8000";   // 后端地址，集中定义

// --- 获取 DOM 元素 ---
const fileInput   = document.getElementById("file-input");
const uploadBtn   = document.getElementById("upload-btn");
const consolidateBtn = document.getElementById("consolidate-btn");
const newSessionBtn = document.getElementById("new-session-btn");
const profileBtn    = document.getElementById("profile-btn");
const messagesEl = document.getElementById('messages')
const queryForm   = document.getElementById("query-form");
const questionInput  = document.getElementById("question");
const documentsEl = document.getElementById("documents");
const base_url = 'http://localhost:8000'

// 追加消息列表
function appendMessage(role, text) {
  const div = document.createElement("div"); //新建<div>节点
  div.className = "message " + role; //设置节点基本信息（可选）
  div.textContent = text; //设置文本属性
  messagesEl.appendChild(div); //插入到dom树
  return div //返回引用
}


// 实现处理SSE流的函数，实际情况一般使用@microsoft/fetch-event-source库代替（需要配置nodejs）
async function streamSSE(url, options, onEvent) {
  const res = await fetch(url, options);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      
      let eventType = "", dataLine = "";
      for (const line of rawEvent.split("\n")) {
        if (line.startsWith("event: ")) eventType = line.slice(7);
        else if (line.startsWith("data: ")) dataLine = line.slice(6);
      }
      
      onEvent(eventType, dataLine);
    }
  }
}

// 问答
async function askQuestion() {
  // 获取<input>的输入内容
  const question = questionInput.value;
  if (!question) return;

  // 追加用户消息
  appendMessage("user", question);

  //追加ai消息
  const aiEl = appendMessage("assistant", "");
  const textNode = document.createTextNode("");
  aiEl.appendChild(textNode);
  
  //接收sse数据
  await streamSSE(
    `${base_url}/api/query`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: currentSessionId }),
    },
    (eventType, dataLine) => {
      if (eventType === "tool") {
        const toolName = JSON.parse(dataLine).name;
        const status = document.createElement("div");
        status.textContent = `调用工具：${toolName}`;
        aiEl.insertBefore(status, textNode);
      } else if (dataLine) {
        textNode.data += JSON.parse(dataLine);
      }
    }
  );
}

// 上传文件
async function uploadFile() {
  const file = fileInput.files[0];
  if (!file) return alert("请先选择 PDF 文件");
  //将文件放到表单数据里
  const form = new FormData();
  form.append("file", file);

  //以表单的形式上传 
  const res = await fetch(`${base_url}/api/ingest`, {
    method: "POST",
    body: form,                  // 注意：不要手动设 Content-Type
  });
  const data = await res.json(); // 后端返回 {doc_id, filename}
  alert(`上传成功：${data.filename}`);
  getDocuments()
}

// 触发记忆整合
async function consolidateMemory() {   // 「整合会话记忆」（consolidate-btn，模块 3 已有）
  const res = await fetch('http://localhost:8000/api/consolidate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSessionId })   // level 缺省即 "L2"，模块 3 的请求体原样兼容
  });
  if (res.status === 422) { alert('该会话还没有可整合的记忆，先对话几轮'); return; }
  const { l2_id } = await res.json();
  alert(`L2 整合完成（${l2_id}）`);
}

async function consolidateProfile() {   // 「整合画像」（profile-btn，本模块新增）
  const res = await fetch('http://localhost:8000/api/consolidate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSessionId, level: "L5" })
  });
  if (res.status === 422) { alert('还没有会话摘要，先整合至少一个会话'); return; }
  const { profile_id } = await res.json();
  alert(`画像更新完成（${profile_id}）`);
}

// 渲染文档列表
async function getDocuments(){
  const res = await fetch(`${base_url}/api/documents`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  const data = await res.json()

  // 清空
  documentsEl.innerHTML = "";
  
  // 插入<p>标签
  data.forEach(doc => {
    const p = document.createElement("p");
    p.textContent = `${doc.filename}`;
    documentsEl.appendChild(p);
  });
}


let currentSessionId = localStorage.getItem("session_id") || crypto.randomUUID();
localStorage.setItem("session_id", currentSessionId);

function newSession() {
  currentSessionId = crypto.randomUUID();
  localStorage.setItem("session_id", currentSessionId);
  messagesEl.innerHTML = "";   // 清空聊天区（messagesEl 是模块 3 已取的元素引用）
}

// 绑定事件
uploadBtn.addEventListener("click", uploadFile); //上传文件
consolidateBtn.addEventListener("click", consolidateMemory);//记忆整合
newSessionBtn.addEventListener("click", newSession);//新会话
profileBtn.addEventListener("click", consolidateProfile);//画像整合
queryForm.addEventListener("submit", (e) => {//发送问题（表单提交事件）
  e.preventDefault();        // 阻止表单默认提交（刷新页面）
  askQuestion();
});


// 页面初始化后调用
getDocuments()