class PluginMixin(object):

    def get_view(self, view_class, opts=None):
        """
        Instantiates and returns the view class that will generate the
        actual context for this plugin.
        """
        kwargs = {}
        # TODO: Should also include parent classes' attributes 
        valid_options = view_class.__dict__.keys()
        if opts:
            if not isinstance(opts, dict):
                opts = opts.__dict__
        else:
            opts = {}

        for key in valid_options:
            if key in opts:
                kwargs[key] = opts[key]
            elif hasattr(self, key):
                kwargs[key] = getattr(self, key)

        view = view_class(**kwargs)
        return view 
