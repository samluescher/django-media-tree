"""
You can use Mixins as superclasses for your custom plugins when
interfacing with third-party applications, such as Django CMS. Please
take a look at :ref:`custom-plugins-howto` for more information.

Basically, a Mixin classes adds methods to your own class (which is
subclassing a Mixin) for instantiating View classes. All attributes 
of your own class that also exist in the View class will be used to 
initialize View instances.

For instance, if your custom class has an attribute 
``template_name``, and an attribute with the same name also
exists in the View class, then the View instance's 
``template_name`` attribute will be set accordingly.

Please refer to :ref:`generic-views` for an overview of attributes you can
define.
"""

VALID_MIXIN_OPTIONS = {}

class PluginMixin(object):

    def get_view(self, request, view_class, opts=None):
        """
        Instantiates and returns the view class that will generate the
        actual context for this plugin.
        """
        kwargs = {}
        if opts:
            if not isinstance(opts, dict):
                opts = opts.__dict__
        else:
            opts = {}

        if not view_class in VALID_MIXIN_OPTIONS:
            valid_options = view_class.__dict__.keys()
            for cls in view_class.__bases__:
                if cls != object:
                    valid_options += cls.__dict__.keys()
            VALID_MIXIN_OPTIONS[view_class] = valid_options

        for key in VALID_MIXIN_OPTIONS[view_class]:
            if key in opts:
                kwargs[key] = opts[key]
            elif hasattr(self, key):
                kwargs[key] = getattr(self, key)

        view = view_class(**kwargs)
        view.request = request
        view.kwargs = {}
        return view 
