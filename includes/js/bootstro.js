/**
 * Bootstro.js Simple way to show your user around, especially first time users 
 * Http://github.com/clu3/bootstro.js
 * 
 * Credit thanks to 
 * Revealing Module Pattern from 
 * http://enterprisejquery.com/2010/10/how-good-c-habits-can-encourage-bad-javascript-habits-part-1/
 * 
 * Bootstrap popover variable width
 * http://stackoverflow.com/questions/10028218/twitter-bootstrap-popovers-multiple-widths-and-other-css-properties
 * 
 */

$(document).ready(function(){
    //Self-Executing Anonymous Func: Part 2 (Public & Private)
    (function( bootstro, $, undefined ) {
        var $elements; //jquery elements to be highlighted
        var count;
        var popovers = []; //contains array of the popovers data
        var activeIndex = null; //index of active item

        var defaults = {
            nextButtonText : 'Next &raquo;', //will be wrapped with button as below
            //nextButton : '<button class="btn btn-primary btn-mini bootstro-next-btn">Next &raquo;</button>',
            prevButtonText : '&laquo; Prev',
            //prevButton : '<button class="btn btn-primary btn-mini bootstro-prev-btn">&laquo; Prev</button>',
            finishButtonText : '<i class="icon-ok"></i> Ok I got it, get back to the site',
            //finishButton : '<button class="btn btn-mini btn-success bootstro-finish-btn"><i class="icon-ok"></i> Ok I got it, get back to the site</button>',
            stopOnBackdropClick : true,
            stopOnEsc : true,
            
            //onComplete : function(params){} //params = {idx : activeIndex}
            //onExit : function(params){} //params = {idx : activeIndex}
            //onStep : function(params){} //params = {idx : activeIndex, direction : [next|prev]}
            //url : String // ajaxed url to get show data from
            
            margin : 100, //if the currently shown element's margin is less than this value
            // the element should be scrolled so that i can be viewed properly. This is useful 
            // for sites which have fixed top/bottom nav bar
        };
        var settings;
        
        
        //===================PRIVATE METHODS======================
        //http://stackoverflow.com/questions/487073/check-if-element-is-visible-after-scrolling
        function is_entirely_visible($elem)
        {
            var docViewTop = $(window).scrollTop();
            var docViewBottom = docViewTop + $(window).height();

            var elemTop = $elem.offset().top;
            var elemBottom = elemTop + $elem.height();

            return ((elemBottom >= docViewTop) && (elemTop <= docViewBottom)
              && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop) );
        }
        
        //add the nav buttons to the popover content;
        
        function add_nav_btn(content, i)
        {
            var $el = get_element(i);
            var nextButton, prevButton, finishButton;
            
            content = content + "<div class='bootstro-nav-wrapper'>";
            if ($el.attr('data-bootstro-nextButton'))
            {
                nextButton = $el.attr('data-bootstro-nextButton');
            }
            else if ( $el.attr('data-bootstro-nextButtonText') )
            {
                nextButton = '<button class="btn btn-primary btn-mini bootstro-next-btn">' + $el.attr('data-bootstro-nextButtonText') +  '</button>';
            }
            else 
            {
                if (typeof settings.nextButton != 'undefined' /*&& settings.nextButton != ''*/)
                    nextButton = settings.nextButton;
                else
                    nextButton = '<button class="btn btn-primary btn-mini bootstro-next-btn">' + settings.nextButtonText + '</button>';
            }
            
            if ($el.attr('data-bootstro-prevButton'))
            {
                prevButton = $el.attr('data-bootstro-prevButton');
            }
            else if ( $el.attr('data-bootstro-prevButtonText') )
            {
                prevButton = '<button class="btn btn-primary btn-mini bootstro-prev-btn">' + $el.attr('data-bootstro-prevButtonText') +  '</button>';
            }
            else 
            {
                if (typeof settings.prevButton != 'undefined' /*&& settings.prevButton != ''*/)
                    prevButton = settings.prevButton;
                else
                    prevButton = '<button class="btn btn-primary btn-mini bootstro-prev-btn">' + settings.prevButtonText + '</button>';
            }
            
            if ($el.attr('data-bootstro-finishButton'))
            {
                finishButton = $el.attr('data-bootstro-finishButton');
            }
            else if ( $el.attr('data-bootstro-finishButtonText') )
            {
                finishButton = '<button class="btn btn-primary btn-mini bootstro-finish-btn">' + $el.attr('data-bootstro-finishButtonText') +  '</button>';
            }
            else 
            {
                if (typeof settings.finishButton != 'undefined' /*&& settings.finishButton != ''*/)
                    finishButton = settings.finishButton;
                else
                    finishButton = '<button class="btn btn-primary btn-mini bootstro-finish-btn">' + settings.finishButtonText + '</button>';
            }

        
            if (count != 1)
            {
                if (i == 0)
                    content = content + nextButton;
                else if (i == count -1 )
                    content = content + prevButton;
                else 
                    content = content + nextButton + prevButton
            }
            content = content + '</div>';
              
            content = content +'<div class="bootstro-finish-btn-wrapper">' + finishButton + '</div>';
            return content;
        }
        
        //get the element to intro at stack i 
        get_element = function(i)
        {
            //get the element with data-bootstro-step=i 
            //or otherwise the the natural order of the set
            if ($elements.filter("[data-bootstro-step=" + i +"]").size() > 0)
                return $elements.filter("[data-bootstro-step=" + i +"]");
            else 
            {
                return $elements.eq(i);
                /*
                nrOfElementsWithStep = 0;
                $elements.filter("[data-bootstro-step!='']").each(function(j,e){
                    nrOfElementsWithStep ++;
                    if (j > i)
                        return $elements.filter(":not([data-bootstro-step])").eq(i - nrOfElementsWithStep);
                })
                */
            }
        }
        
        get_popup = function(i)
        {
            var p = {};
            var $el = get_element(i);
            //p.selector = selector;
            var t = '';
            if (count > 1)
            {
                t = "<span class='label label-success'>" + (i +1)  + "/" + count + "</span>";
            }
            p.title = $el.attr('data-bootstro-title') || '';
            if (p.title != '' && t != '')
                p.title = t + ' - ' + p.title;
            else if (p.title == '') 
                p.title = t;

            p.content = $el.attr('data-bootstro-content') || '';
            p.content = add_nav_btn(p.content, i);
            p.placement = $el.attr('data-bootstro-placement') || 'top';
            var style = ''; 
            if ($el.attr('data-bootstro-width'))
            {
                p.width = $el.attr('data-bootstro-width'); 
                style = style + 'width:' + $el.attr('data-bootstro-width') + ';'
            }
            if ($el.attr('data-bootstro-height'))
            {
                p.height = $el.attr('data-bootstro-height');
                style = style + 'height:' + $el.attr('data-bootstro-height') + ';'
            }
            p.trigger = 'manual'; //always set to manual.
           
            p.html = $el.attr('data-bootstro-html') || 'top';
            
            //resize popover if it's explicitly specified
            //note: this is ugly. Could have been best if popover supports width & height
            p.template = '<div class="popover" style="' + style + '"><div class="arrow"></div><div class="popover-inner"><h3 class="popover-title"></h3><div class="popover-content"><p></p></div></div>' +
             '</div>';
            
            return p;
            
        }

        //===================PUBLIC METHODS======================
        //destroy popover at stack index i
        bootstro.destroy_popover = function(i)
        {
            var i = i || 0;
            if (i != 'all')
            {
                var $el = get_element(i);//$elements.eq(i); 
                $el.popover('destroy').removeClass('bootstro-highlight');
            }
            /*
            else //destroy all
            {
                $elements.each(function(e){
                    
                    $(e).popover('destroy').removeClass('bootstro-highlight');
                });
            }
            */
        };
        
        //destroy active popover and remove backdrop
        bootstro.stop = function()
        {
            bootstro.destroy_popover(activeIndex);
            bootstro.unbind();
            $("div.bootstro-backdrop").remove();
            if (typeof settings.onExit == 'function')
                settings.onExit.call(this,{idx : activeIndex});
        };

        //go to the popover number idx starting from 0
        bootstro.go_to = function(idx) 
        {
            //destroy current popover if any
            bootstro.destroy_popover(activeIndex);
            if (count != 0)
            {
                var p = get_popup(idx);
                var $el = get_element(idx);
                
                $el.popover(p).popover('show');
                  
                //scroll if neccessary
                var docviewTop = $(window).scrollTop();
                var top = Math.min($(".popover.in").offset().top, $el.offset().top);
                
                //distance between docviewTop & min.
                var topDistance = top - docviewTop;
                
                if (topDistance < settings.margin) //the element too up above
                    $('html,body').animate({
                        scrollTop: top - settings.margin},
                    'slow');
                else if(!is_entirely_visible($(".popover.in")) || !is_entirely_visible($el))
                    //the element is too down below
                    $('html,body').animate({
                        scrollTop: top - settings.margin},
                    'slow');
                // html 
                  
                $el.addClass('bootstro-highlight');
                activeIndex = idx;
            }
        };
        
        bootstro.next = function()
        {
            if (activeIndex + 1 == count)
            {
                if (typeof settings.onComplete == 'function')
                    settings.onComplete.call(this, {idx : activeIndex});//
            }
            else 
            {
                bootstro.go_to(activeIndex + 1);
                if (typeof settings.onStep == 'function')
                    settings.onStep.call(this, {idx : activeIndex, direction : 'next'});//
            }
        };
        
        bootstro.prev = function()
        {
            if (activeIndex == 0)
            {
                /*
                if (typeof settings.onRewind == 'function')
                    settings.onRewind.call(this, {idx : activeIndex, direction : 'prev'});//
                */
            }
            else
            {
                bootstro.go_to(activeIndex -1);
                if (typeof settings.onStep == 'function')
                    settings.onStep.call(this, {idx : activeIndex, direction : 'prev'});//
            }
        };
        
        bootstro._start = function(selector)
        {
            selector = selector || '.bootstro';

            $elements = $(selector);
            count  = $elements.size();
            if (count > 0 && $('div.bootstro-backdrop').length === 0)
            {
                // Prevents multiple copies
                $('<div class="bootstro-backdrop"></div>').appendTo('body');
                bootstro.bind();
                bootstro.go_to(0);
            }
        };
        
        bootstro.start = function(selector, options)
        {
            settings = $.extend(true, {}, defaults); //deep copy
            $.extend(settings, options || {});
            //if options specifies a URL, get the intro configuration from URL via ajax
            if (typeof settings.url != 'undefined')
            {
                //get config from ajax
                $.ajax({
                    url : settings.url,
                    success : function(data){
                        if (data.success)
                        {
                            //result is an array of {selector:'','title':'','width', ...}
                            var popover = data.result;
                            //console.log(popover);
                            var selectorArr = [];
                            $.each(popover, function(t,e){
                                //only deal with the visible element
                                //build the selector
                                $.each(e, function(j, attr){
                                    $(e.selector).attr('data-bootstro-' + j, attr);
                                });
                                if ($(e.selector).is(":visible"))
                                    selectorArr.push(e.selector);
                            });
                            selector = selectorArr.join(",");
                            bootstro._start(selector);
                        }
                    }
                });
            }
            else 
            {
                bootstro._start(selector);
            }
            
        };
          
        //bind the nav buttons click event
        bootstro.bind = function()
        {
            bootstro.unbind();
            
            $("html").on('click.bootstro', ".bootstro-next-btn", function(e){
                bootstro.next();
                e.preventDefault();
                return false;
            });
            
            $("html").on('click.bootstro', ".bootstro-prev-btn", function(e){
                bootstro.prev();
                e.preventDefault();
                return false;
            });
      
            //end of show
            $("html").on('click.bootstro', ".bootstro-finish-btn", function(e){
                bootstro.stop();
            });        
            
            if (settings.stopOnBackdropClick)
            {
                $("html").on('click.bootstro', 'div.bootstro-backdrop', function(e){
                    if ($(e.target).hasClass('bootstro-backdrop'))
                        bootstro.stop();
                });
            }
                
            //bind the key event
            $(document).on('keydown.bootstro', function(e){
                var code = (e.keyCode ? e.keyCode : e.which);
                if (code == 39 || code == 40)
                    bootstro.next();
                else if (code == 37 || code == 38)
                    bootstro.prev();
                else if(code == 27 && settings.stopOnEsc)
                    bootstro.stop();
            })
        };
        
        bootstro.unbind = function()
        {
            $("html").unbind('click.bootstro');
            $(document).unbind('keydown.bootstro');
        }
           
     }( window.bootstro = window.bootstro || {}, jQuery ));
});