
function ajaxAssert(destination,message,datacallback) {
	
	function innerFunction() {
		$.get(destination,function(data,msg,response) {
			if (datacallback(data,msg,response)) {
				ok(true);
			} else {
				console.log(data);
				ok(false,message);
			}
			start();
		}).error(function(data) {
			ok(false,"Error on the web");
			start();
		});
	}
	
	innerFunction();
}


$('document').ready(function() {
	
	
	//set up the tests
	$.ajax({
		url:'init.dbpy',
		async:false
		});
	
	
	////////////// basic tests of the dropbox remove and listdir functions
	
	module("Dropbox");
	
		asyncTest("List Dir",function() {
			expect(1);
			ajaxAssert('dropbox/listdir.dbpy',"Directory contents do not match",function(data,msg,response) {
				return data == "listdir.dbpy\nmakedelete.dbpy\n";
			});	

		});
		
		asyncTest("make and delete dir",function() {
			expect(1);
			ajaxAssert('dropbox/makedelete.dbpy',"Error while deleting",function(data,msg,response) {
				return data == "listdir.dbpy\nmakedelete.dbpy\n";
			});

		});
		
	
	/////////////// tests of the IO module
	
	module("IO");
	
	
		asyncTest("Read File",function() {
			expect(1);
			ajaxAssert('files/readfile.dbpy',"Did not read file correctly",function(data,msg,response) {
				return data == "This is a file to test for the ability to read files.\nSecond line.\n";
			});
		});
		asyncTest("Render File",function() {
			expect(1);
			ajaxAssert('files/renderfile.dbpy',"Did not read file correctly",function(data,msg,response) {
				return data == "This is a file to test for the ability to read files.\nSecond line.";
			});
		});
		
		
		asyncTest("Load json",function() {
			expect(1);
			ajaxAssert('files/loadjson.dbpy',"Did not read json correctly",function(data,msg,response) {
				return data == "5\n1\n2\nthree\n";
			});
		});
		
		asyncTest("Render json",function() {
			expect(1);
			ajaxAssert('files/renderjson.dbpy',"Did not render json correctly",function(data,msg,response) {
				return data.id == 5;
			});
		});
		
		asyncTest("Write file",function() {
			expect(1);
			ajaxAssert('files/writefile.dbpy',"Did not correctly write file",function(data,msg,response) {
				return data == "This file was just written.\n";
			});
		});
		
		asyncTest("Save json",function() {
			expect(1);
			ajaxAssert('files/savejson.dbpy',"Did not correctly write json",function(data,msg,response) {
				return data == "it worked\n3\n";
			});
		});
		
		asyncTest("Open file",function() {
			expect(1);
			ajaxAssert('files/openfile.dbpy',"Did not correctly open and write file",function(data,msg,response) {
				return data == "hello there\n";
			});
		});
		
		asyncTest("Open json",function() {
			expect(1);
			ajaxAssert("files/openjson.dbpy","Did not correctly open and write json file",function(data,msg,response) {
				return data == "4\n";
			});
		});
		
	
	/////////////////// tests of the http module
	
	module("HTTP");
	
		asyncTest("Status Code",function() {
			expect(1);
			ajaxAssert('http/status.dbpy',"Response Status not correctly set",function(data,msg,response) {
				return response.status == 255;
			});
		});
	
		asyncTest("Set Headers",function() {
			expect(1);
			ajaxAssert('http/setheader.dbpy',"Response header not correctly set!",function(data,msg,response) {
				return response.getResponseHeader("X-dbpy-test") == "ok";
			});
		});
	
		asyncTest("Get Headers",function() {
			expect(1);
			$.ajax('http/getheader.dbpy',{
				headers: {'x-dbpy-test':'ok'},
				success: function(data) {
					if (data == "ok\n") {
						ok(true);
					} else {
						console.log(data);
						ok(false,"headers not get correctly");
					}
					start();
				},
				error: 	function(ob,mes,err) {
					ok(false,"Error on the web");
					start();
				}
			
			});

		});
	
		asyncTest("Redirect",function() {
			expect(1);
			ajaxAssert('http/redirect.dbpy',"Redirect unsuccessful",function(data,msg,response) {
				return data == "you've been redirected!\n";
			});
		});
		
		asyncTest("Error",function() {
			expect(1);
			$.ajax('http/errorresponse.dbpy',{
				success: function(data) {
					ok(false,"this was supposed to be an error!");
				},
				error: 	function(ob,mes,err) {
					ok(true,"Sweet, an error");
					start();
				}
			
			});

		});
		
		asyncTest("Get Params",function() {
			expect(1);
			ajaxAssert('http/getparams.dbpy?foo=bar&list=1&list=2',"Get Params not working",function(data,msg,response) {
				return data == "bar\n1,2\n"
			})
		})
		
		asyncTest("Post Params",function() {
			expect(1);
			$.ajax('http/postparams.dbpy',{
				data:"foo=bar&list=1&list=2",
				type:"POST",
				success: function(data) {
					if (data == "bar\n1,2\n") {
						ok(true);
					} else {
						console.log(data);
						ok(false,"post params not working");
					}
					start();
				},
				error: 	function(ob,mes,err) {
					ok(false,"Error on the web");
					start();
				}
			
			});

		});
		
	module("Sessions")
	
		asyncTest("Write Session",function() {
			expect(1);
			
			$.ajax('sessions/write.dbpy',{
				type:"GET",
				async:false
			});
			
			ajaxAssert('sessions/read.dbpy',"Reading session",function(data,msg,response) {
				return data == "ok\n"
			});		
		});

		asyncTest("Clear Session",function() {
			expect(1);
			
			$.ajax('sessions/write.dbpy',{
				type:"GET",
				async:false
			});
			
			ajaxAssert('sessions/clear.dbpy',"Clearing session",function(data,msg,response) {
				return data == "not there\n"
			});		
		});
		
		asyncTest("Multi request session",function() {
			expect(1);
			$.ajax('sessions/clear.dbpy',{
				type:"GET",
				async:false
			});
			
			$.ajax('sessions/incr.dbpy',{
				type:"GET",
				async:false
			});
			$.ajax('sessions/incr.dbpy',{
				type:"GET",
				async:false
			});
			$.ajax('sessions/incr.dbpy',{
				type:"GET",
				async:false
			});
			$.ajax('sessions/incr.dbpy',{
				type:"GET",
				async:false
			});
			
			ajaxAssert('sessions/read.dbpy',"Reading session",function(data,msg,response) {
				return data == "4\n"
			});
		});
		
		
	module("Templates");
	
		asyncTest('Simple Template',function() {
			expect(1);
			ajaxAssert('templates/simple.dbpy',"Simple Template",function(data,msg,response) {
				return data == "ok\n";
			});
		});
	
		asyncTest("Template with Inheritence",function() {
			expect(1);
			ajaxAssert('templates/inherits.dbpy',"Inherits Template",function(data,msg,response) {
				return data == "extends-ok\n";
			});
		});
		
	module("Imports");
	
		asyncTest("Simple Import",function() {
			expect(1);
			ajaxAssert('imports/simple.dbpy',"Simple Import",function(data,msg,response) {
				return data == "hello from imported file\n";
			});
		});
		
		asyncTest("Nested Import",function() {
			expect(1);
			ajaxAssert('imports/meta.dbpy',"Nested Import",function(data,msg,response) {
				return data == "hello from imported file\n";
			});
		});
		
		asyncTest("Multi-Import",function() {
			expect(1);
			ajaxAssert('imports/multi.dbpy',"Multi Import",function(data,msg,response) {
				return data == "hello from imported file\n9\nolleh\n"
			});
		});
		
	module("Background");
	
		asyncTest("Background Request",function() {
			expect(2);
			$.ajax('background/bg_trigger.dbpy',{
				method:'get',
				async:false
			});
			ok(true,"background request triggered");
			
			//then give it time to happen
			setTimeout(function() {
				ajaxAssert('background/bg_written.txt',"Background request not triggered",function(data,msg,response) {
					return data == "ok\n";
				});
			},10000);
		
		
		});
	
});


