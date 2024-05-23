const express = require('express');
const axios = require('axios');
var es = require('./modules/es/persist');
const path = require('path'); // Import path module
const app = express();
const PORT = process.env.PORT || 3000;
const es_index_feedback = "doc_qna_feedback"
const es_index_conversation = "doc_qna_conversation"
const quiz_gen = require('./modules/quiz/quiz_gen')
const timestamp = require('time-stamp');
const fs = require('fs');

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
        const data = {'query': req.body.data.query, 'response' : response.data}
        await es.saveToEDB(data, req.body.user_name, req.body.machine_id, es_index_conversation, (err, res)=>{
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

app.post('/generate/quiz', async (req, res) => {
    try {
        ts = timestamp('YYYYMMDDss')
        console.log(req.body.resource_name)
        id = req.body.resource_name + "_" + ts
        console.log(req.body.content)
        console.log(req.body.num_questions)
        console.log(req.body.num_options)
        console.log(req.body.machine_id)
        console.log(req.body.userName)
        quiz_gen.generate_quiz(req.body.num_questions, req.body.num_options, req.body.content, (err, resp)=>{
            if(err){
                res.status(500).json({ error: err });
            }else{
                fs.writeFile('data/' + id + '.json', JSON.stringify(resp),(error)=>{
                    if(error){
                        console.log(error)
                        return
                    }
                    console.log("written " + id + ".json to disk")
                })
            }
        })
        res.json({"message" : "quiz generation request submitted, use the request token to access quiz once generated" , "token" : id});
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.post('/get/quiz', async (req, res) => {
    try {
        console.log(req.body.quiz_id)
        file_path = './data/' + req.body.quiz_id + '.json'
        console.log(file_path)
        console.log(fs.existsSync(file_path))
        if(fs.existsSync(file_path)){
            await res.setHeader('Content-disposition', 'attachment; filename=' + req.body.quiz_id + '.json');
            await res.setHeader('Content-type', 'Content-Type: application/json');
            await res.download(file_path, (error)=>{
            console.log(error)
           })
        }else{
            res.status(404).json({ error: 'Quiz file seems to be unavailble. If you have submitted recently, kindly check back later.' });
        }
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal Server Error' });
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
