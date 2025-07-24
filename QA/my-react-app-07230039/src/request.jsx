import axios from 'axios';

const SERVER_PATH = "http://localhost:8001"

export async function profile(token) {
  //  const response = axios.get(SERVER_PATH + "/profile/", {
  //   headers: {
  //     Authorization: `Bearer ${token}`
  //   }
  // });
  // return response;
    return {"data":{"username":"Tom", "email":"Tom@tom.com", "id":"0"}};
}


export async function register(username, email, password) {
    const response = await axios.post(SERVER_PATH + "/api/auth/register/", {
        username:username,
        email:email,
        password:password
    });
    return response;
}


export async function login(username, password) {
    const response = await axios.post(SERVER_PATH + "/api/auth/token/", {
        username:username,
        password:password
    });
    return response;
}

export async function token(username, password) {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await axios.post(SERVER_PATH + '/token', params, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });

    return response;
}

export async function aisk(token, question, conversationId = null, files = []) {
    const form = new FormData();

    // 1. JSON 部分
    form.append('question', question);
    // console.log("InAPI "+conversationId);
    if (conversationId) form.append('conversation_id', conversationId);

    // 2. 文件部分（可 0~N 个）
    files.forEach(f => form.append('files', f));

    const { data } = await axios.post(SERVER_PATH + '/api/aisk', form, {
        headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`
        }
    });
    return data;
}

export async function all_conversations(token) {
    return await axios.get(SERVER_PATH + '/api/conversations', {
        headers: {
            Authorization: `Bearer ` + token
        }
    });
}

export async function get_conversations(token, id) {
    return await axios.get(SERVER_PATH + '/api/conversations/' + id, {
        headers: {
            Authorization: `Bearer ` + token
        }
    });
}

export async function delete_conversation(token, id) {
    const response = axios.delete(SERVER_PATH + '/api/conversations/' + id, {
        headers: {
            Authorization: `Bearer ` + token
        }
    })
    return response;
}

export async function updateTitle(token, conversationId, newTitle) {
    const response = await fetch(SERVER_PATH + `/api/conversations/${conversationId}/title`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': `Bearer ${token}`
        },
        body: `new_title=${encodeURIComponent(newTitle)}`
    });
    return await response.json();
}

