// =============== Flex slider functions =============== //

	function flexSliderCaption(){
		$('.flexslider .slides li')
			.mouseenter(function(){
				$(this).find('.flex-caption').stop().animate({
						opacity : 1
					} , 500);
			})
			.mouseleave(function(){
				$(this).find('.flex-caption').stop().animate({
						opacity : 0
					} , 500);
			});	
	}
	
	function setupFlexSlider(){
		 $('.flexslider').flexslider({
			animation: "slide",                
			slideshow: false, 
			startAt: 1
		  });
	}
	
// =============== Flex slider functions END =============== //

