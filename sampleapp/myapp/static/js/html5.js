var createNonSupportedElement = function() {
    var tags = ['header', 'nav', 'article', 'section', 'aside', 'footer'];
    for (var i = 0, len = tags.length; i < len; i++) {
        document.createElement(tags[i]);
    }
};
