define("paging", ['jquery'],
function($) {

    var page = 1;
    var limit = 25;
    var itemCount = 0;
    var callback = null;

    /*
     * config()
     */
    function config(data) {
        var count = data['item-count'];
        if (count != null) {
            itemCount = count;
            $('.paging span.item-count span').html(itemCount);
            $('.paging .page-number').html(page);
            $('.paging .page-count').html(getPageCount());
        }
        show();
    }

    /*
     * bind()
     * Enable the next, previous, etc links.
     */
    function bind(cb) {
        callback = (cb != null) ? cb : null;
        $('.paging .next a').off('click');
        $('.paging .next a').bind('click', next);
        $('.paging .previous a').off('click');
        $('.paging .previous a').bind('click', prev);
        $('.paging .first a').off('click');
        $('.paging .first a').bind('click', first);
        $('.paging .last a').off('click');
        $('.paging .last a').bind('click', last);
    }

    /*
     * getPageCount()
     */
    function getPageCount() {
        var n = (itemCount + limit -1) / limit;
        return Math.floor(n);
    }

    /*
     * getPageNumber()
     */
    function getPageNumber() {
        return page;
    }

    /*
     * getItemCount()
     */
    function getItemCount() {
        return itemCount;
    }

    /*
     * set(n)
     */
    function set(n) {
        page = n;
        $('.paging .page-number').html(page);
        if (callback != null) {
            callback(n);
        }
    }

    /*
     * next()
     * Go to the next page if available.
     */
    function next(event) {
        if (event != null) {
            event.preventDefault();
            event.stopPropagation();
        }
        if (page < getPageCount()) {
            set(page + 1);
        }
    }

    /*
     * prev()
     */
    function prev(event) {
        if (event != null) {
            event.preventDefault();
            event.stopPropagation();
        }
        if (page > 1) {
            set(page - 1);
        }
    }

    /*
     * first()
     */
    function first(event) {
        if (event != null) {
            event.preventDefault();
            event.stopPropagation();
        }
        set(1);
    }

    /*
     * next()
     */
    function last(event) {
        if (event != null) {
            event.preventDefault();
            event.stopPropagation();
        }
        set(getPageCount());
    }

    /*
     * show()
     */
    function show() {
        if (itemCount > 0) {
            $('.paging .count, .paging .first, .paging .previous').show();
            $('.paging .numbering, .paging .next, .paging .last').show();
        } else {
            hide();
        }
        $('.paging').css('display','inline-block');
    }

    /*
     * hide()
     */
    function hide() {
        /* always show the item count */
        $('.paging first').hide();
        $('.paging .first, .paging .previous').hide();
        $('.paging .numbering, .paging .next, .paging .last').hide();
    }
    
    return {'limit': limit, /* read-only */
            'getItemCount': getItemCount,
            'getPageCount': getPageCount,
            'getPageNumber' : getPageNumber,
            'config': config,
            'bind': bind,
            'set': set,
            'prev': prev,
            'next': next,
            'first': first,
            'last': last,
            'show': show,
            'hide': hide
           }
});
