var request = require('request');



function generate_quiz(q_num, opt_num, content, cb) {
    if (!opt_num) opt_num = 4;
    if (!q_num) q_num = 10;
    var options = {
        'method': 'POST',
        'url': 'http://localhost:11434/api/chat',
        'headers': {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "model": "quiz_master",
            "messages": [
                {
                    "role": "user",
                    "content": "generate a quiz from the content inside curly braces. number of questions will be "+ q_num +" . each question should have exactly "+ opt_num +" options with one correct answer. respond in json format and response should only contain json. mention the referred text in question wherever need be. {" + content+"}"
                }
            ],
            "stream": false
        })

    };
    request(options, function (error, response) {
        if (error) cb(error, null);
        console.log(JSON.parse(JSON.parse(response.body).message.content));
        cb(null, JSON.parse(JSON.parse(response.body).message.content))
    });

}


module.exports.generate_quiz = generate_quiz