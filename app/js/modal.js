define(['jquery'],
function ($)
{
    //'use strict';
    /*
     * Modals are automatically attached to any element with:
     *   data-toggle='modal-popup'
     * FIXME: use the bootstrap modals...
     *
     * Settings (via $().data('key', value) or data-key=value):
     *   closeOnConfirm: dismiss the dialog automatically after confirm
     *   target: the id of the dialog, defaults to '#okcancel'.
     *   show: function that is called before the dialog is displayed.
     *         returning false prevents the dialog from being shown at all.
     *   confirm: callback when ok, save, etc is selected (required).
     */

    function Modal(element, settings) {
        var $this = $(this);
        this.$element = $(element);

        /* BEGIN settings */
        this.closeOnConfirm = true;
        this.target = 'okcancel';

        this.show = function(modal) {
            return true;
        }

        this.confirm = function(modal) {
            throw "The modal element is missing a 'confirm' callback.";
        }

        $.extend(this, settings);
        /* END settings */

        this.$target = $('#' + this.target); /* the DOM of the dialog itself */

        this.click = function() {
            /* FIXME: test the $dialog selector */
            if (this.$element.hasClass('inactive')) {
                return;
            }
            /* should the modal be shown or not */
            if (!this.show()) {
                return;
            }

            var modal = this;
            $('.ok, .cancel, .shade').off('click');
            $('.ok', this.$target).on('click', function() {
                modal.confirm();
                if (modal.closeOnConfirm) {
                    modal.$target.removeClass('visible');
                }
            });

            /* setup cancel button and click on the shade. */
            $('.cancel, .shade', this.$target).bind('click', function() {
                modal.$target.removeClass('visible');
            });

            /* set the modal text */
            if (this.text != null) {
                $('p', this.$target).html(this.text);
            }
            this.$target.addClass('visible');
        }
    }

    $(document).on('click.modal-popup.data-api', '[data-toggle="modal-popup"]', function (evt) {
        var modal = $(this).data('palette.modal');
        if (!modal) {
            modal = new Modal(this, $(this).data());
            $(this).data('palette.modal', modal);
        }
        modal.click();
    });
                       
});
