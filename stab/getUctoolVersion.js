var system = require('system');
var args = system.args;

var page = require('webpage').create();
page.viewportSize = { width: 1024, height: 768 };

var up = args[1];
var rev = args[2];

var reUpG2 = /CXP9024418|CXP9028754/;
var rootUrl = reUpG2.test(up) ? 'https://rbs-g2-mia.rnd.ki.sw.ericsson.se/' : 'https://lmr-g1-ci-mia.rnd.ki.sw.ericsson.se/';


var url = rootUrl + 'login/';
var dataurl = rootUrl + 'products/' + up + '/revision/' + rev + '/';


//console.log(dataurl)



function getData() {
    page.open(dataurl, function (status) {

	// console.log('Get data page status: ' + status);
	setTimeout(function () {
	    var c = page.evaluate(function () {
		return $("td:contains('lrat_uctool_version')").next().text();
	    });

	    console.log(c.trim());
	    page.render('login.png');
	    
	    phantom.exit();

	}, 6000);
    });
}

function onPageReady() {

    page.evaluate(function () {
	$("input[name='guestLogin']").click();
	$("#login-submit-button").click();
    });

    // console.log("screenshot login page!!");
    page.render('logout.png');
    setTimeout(function () {
	// console.log("Waiting for login!!!!");
	getData();
    }, 3000);


}

page.open(url, function (status) {
    function checkReadyState() {
        setTimeout(function () {
            var readyState = page.evaluate(function () {
                return document.readyState;
            });

            if ("complete" === readyState) {
                onPageReady();
            } else {
                checkReadyState();
            }
        }, 2000);
    }
    // console.log('!!!Get login page status: ' + status)

    checkReadyState();

});

