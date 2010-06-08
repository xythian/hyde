
var userPattern = /@([a-zA-Z0-9]+) /g;
var hashPattern = /\#([a-zA-Z0-9]+)/g;

function linkifyTweet(text) {
    text = text.replace(userPattern, "<a href='http://twitter.com/$1' target='_blank'>@$1</a> ");
    text = text.replace(hashPattern, "<a href='http://twitter.com/search?q=%23$1' target='_blank'>#$1</a>")
    return text;
}


function refreshTweets() {

    $.getJSON("http://twitter.com/status/user_timeline/snorp.json?count=10&callback=?", function(data){
        $("#tweet_container").html("<ul></ul>");
        
        $.each(data, function(i,item) {
            var tweet = document.createElement('li');
            tweet.innerHTML = linkifyTweet(item.text);
            tweet.setAttribute('class', 'tweet');
            tweet.setAttribute('tweet_id', item.id);
            $("#tweet_container ul").append(tweet);
        });
        
        $(".tweet").click(function(event) {
            var tweet_id = event.target.getAttribute('tweet_id');
            
            if (tweet_id) {
                window.open('http://twitter.com/snorp/status/' + event.target.getAttribute('tweet_id'));
            }
        });
    });

}


// Load jQuery
google.load("jquery", "1");

google.setOnLoadCallback(function() {
    refreshTweets();
})