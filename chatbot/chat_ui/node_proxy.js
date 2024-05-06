const express = require('express');
const axios = require('axios');
var es = require('./modules/es/persist');
const path = require('path'); // Import path module
const app = express();
const PORT = process.env.PORT || 3000;
const es_index_feedback = "doc_qna_feedback"
const es_index_conversation = "doc_qna_conversation"
app.use(express.json());

// CORS middleware
app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    if (req.method === 'OPTIONS') {
        // Respond to preflight requests
        res.sendStatus(200);
    } else {
        // Continue to next middleware
        next();
    }
});

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

// Proxy endpoint
app.post('/proxy', async (req, res) => {
    console.log('got the request.....')
    console.log(req.body)
    try {
        const response = await axios.post(req.body.url, req.body.data);
        data = {'request': req.body, 'response' : response}
        es.saveToEDB(data, req.body.user_name, req.body.machine_id, es_index_conversation, (err, res)=>{
            if(err){
                console.log(err)
            }else{
                console.log(res)
            }
        })
        res.json(response.data);
    } catch (error) {
        console.error(error);
        res.json({"generated_ans" : "proxy server: failed to connect to backend"});
        //res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.post('/gather/feedback', async (req, res) => {
    try {
        console.log(req.body.feedback)
        console.log(req.body.question)
        console.log(req.body.answer)
        console.log(req.body.machine_id)
        console.log(req.body.userName)
        es.saveToEDB(req.body, req.body.user_name, req.body.machine_id, es_index_feedback, (err, res)=>{
            if(err){
                console.log(err)
            }else{
                console.log(res)
            }
        })
        res.sendStatus(200)
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
