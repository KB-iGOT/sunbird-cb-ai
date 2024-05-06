var client     =     require('./connection')



function saveToEDB(data, created_by, session_id, es_index, cb){
	console.log('http://'+process.env.APP_ES_USERNAME+':'+process.env.APP_ES_PASSWORD+'@'+process.env.APP_ES_HOST + ':' + process.env.APP_ES_PORT)

	var index = es_index;
	//var index = session_id.split("_")[0]
	console.log(index);
	//index = "thor_"+index.toLowerCase();
  	client.cluster.health({},function(err,resp,status)
  {  
  	console.log("-- Client Health --",resp.status);
	if(resp.status != 'red'){
           data['session_id'] = session_id
	   data['created_by'] = created_by
	   data['user'] = session_id
	   client.index({
		   index : index,
		   body  : data
	   },(err, resp, status)=>{
		   if(err){
		     console.log(err)
		   }else{
			console.log(resp)
		   }
	   });
	}
	cb(null,resp)
      }); 
}


module.exports.saveToEDB    = saveToEDB;
