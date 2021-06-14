from ipyleaflet import WMSLayer
from ipywidgets import HTML, Dropdown, Layout, SelectionSlider, VBox, HBox, Checkbox, Button
from owslib.wms import WebMapService
from projections import get_common_crs, get_projection
from traitlets import Unicode
import xml.etree.ElementTree as ET


class ZTWMSLayer(WMSLayer):
    time = Unicode("").tag(sync=True, o=True)
    elevation = Unicode("").tag(sync=True, o=True)
    styles = Unicode("").tag(sync=True, o=True)
    ipygis_key = Unicode("").tag(sync=True, o=True)
    # logscale = Bool(True).tag(sync=True, o=True)


def get_center(wms):
    w, s, e, n = wms.contents[list(wms.contents)[0]].boundingBoxWGS84
    width = max(w, e) - min(w, e)
    height = max(s, n) - min(s, n)
    center = round(min(s, n) + height / 2, 4), round(min(w, e) + width / 2, 4)
    return center


def get_png_legend(legend):
    return f'<div id="img" style="float:left"><img style="horizontal-align:top" src="{legend}" width="80%" alt=""></div>'


def get_wms_layers(wms):
    wms_layers = list(set(list(wms.contents)) - set(["WMS", "lat", "lon"]))
    wms_layers.sort()
    return wms_layers


def get_wms_name(wms):
    name = ET.fromstring(wms.getServiceXML().decode()).findall('.//*Layer')[0].findall('.//*Title')[0].text,


def get_ztwms(wms_url, crs, ipygis_key):
    wms = WebMapService(wms_url)
    wms_layers = get_wms_layers(wms)
    if wms.contents[wms_layers[0]].timepositions:
        time = wms.contents[wms_layers[0]].timepositions[1]
    else:
        time = ""
    if wms.contents[wms_layers[0]].elevations:
        elevation = wms.contents[wms_layers[0]].elevations[1]
    else:
        elevation = "0"
    crs = get_projection(crs)
    ztwms = ZTWMSLayer(
        # name=wms.contents[wms_layers[0]].title,
        name=ET.fromstring(wms.getServiceXML().decode()).findall('.//*Layer')[0].findall('.//*Title')[0].text,
        url=wms_url,
        layers=wms_layers[0],
        time=time,
        elevation=elevation,
        format="image/png",
        styles="",
        transparent=True,
        attribution="R&D RS@met.no © 2021",
        crs=crs,
        ipygis_key=ipygis_key,
    )
    return ztwms, wms, wms_layers


class ztwms_control(object):
    def __init__(self, wms_url, crs, m=None, ipygis_key=None):
        self.wms_url = wms_url
        self.crs = crs
        self.ipygis_key = ipygis_key
        self.ztwms, self.wms, self.wms_layers = get_ztwms(self.wms_url, self.crs, self.ipygis_key)
        self.wms_control = self.get_wms_controls()
        self.m = m

    def get_wms_controls(self):
        # layer_header = HTML()
        layer_header = Checkbox(
            value=True,
            description=f"<b>{self.ztwms.name}</b>",
            disabled=False,
            indent=False,
            # layout=Layout(max_width="380px", max_height="35px")
        )
        header = HBox([layer_header],
                      layout=Layout(min_width="380px", min_height="45px")
                      )
        layer_header.observe(self.update_wms_visibility)
        # layer_footer = HTML()
        # layer_footer.value = '<br>'
        # WMS Layer selection
        layer_selector = Dropdown(
            options=self.wms_layers,
            value=self.wms_layers[0],
            description='<font style="text-align:left;"><b>Layer:</b></font>',
            # layout=Layout(max_width="380px", max_height="35px"),
        )
        layer_selector.observe(self.update_wms_layer, "value")
        # WMS Opacity slider
        op_range = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
        opacity_slider = SelectionSlider(
            description="<b>Opacity:</b>",
            options=op_range,
            orientation="horizontal",
            value=1,
            # layout=Layout(max_width="380px", max_height="35px"),
        )
        opacity_slider.observe(self.update_wms_opacity, "value")
        # WMS TIME
        if self.wms.contents[layer_selector.value].timepositions:
            time_slider = SelectionSlider(
                description="<b>Time:</b>",
                options=self.wms.contents[layer_selector.value].timepositions,
                # layout=Layout(max_width="380px", max_height="35px"),
            )
            time_slider.layout.visibility = "visible"
            # print(self.wms.contents[layer_selector.value].timepositions)
        else:
            time_slider = SelectionSlider(
                description="<b>Time:</b>",
                options=[""],
                # layout=Layout(max_width="380px", max_height="35px"),
            )
            time_slider.layout.visibility = "hidden"
        time_slider.observe(self.update_wms_time, "value")
        # WMS Elevation
        if self.wms.contents[layer_selector.value].elevations:
            elevation_slider = SelectionSlider(
                description="<b>Elevation:</b>",
                options=self.wms.contents[layer_selector.value].elevations,
                # layout=Layout(max_width="380px", max_height="35px"),
            )
            elevation_slider.layout.visibility = "visible"
            # print(self.wms.contents[layer_selector.value].elevations)
        else:
            elevation_slider = SelectionSlider(
                description="<b>Elevation:</b>",
                options=[""],
                # layout=Layout(max_width="380px", max_height="35px"),
            )
            elevation_slider.layout.visibility = "hidden"
        elevation_slider.observe(self.update_wms_elevation, "value")
        # WMS Styles
        if self.wms.contents[layer_selector.value].styles:
            styles_selector = Dropdown(
                description="<b>Style:</b>",
                options=list(self.wms.contents[layer_selector.value].styles.keys()),
                # layout=Layout(max_width="380px", max_height="35px"),
            )
            styles_selector.layout.visibility = "visible"
            wms_legend = HTML(
                get_png_legend(
                    self.wms.contents[layer_selector.value].styles[
                        list(self.wms.contents[layer_selector.value].styles.keys())[0]
                    ]["legend"]
                )
            )
        else:
            styles_selector = Dropdown(description="Style:", options=[""])
            styles_selector.layout.visibility = "hidden"
            wms_legend = HTML(f"")
        styles_selector.observe(self.update_wms_styles, "value")
        styles_selector.observe(self.update_wms_legend, "value")

        return VBox(
            [
                #layer_header,
                header,
                layer_selector,
                opacity_slider,
                styles_selector,
                time_slider,
                elevation_slider,
                wms_legend,
            ],  # layout=Layout(border='solid 1px', min_height="200px", display='block')
        )

    def map_interact_up(self, change):
        maplayers = list(self.m.layers)[::-1]
        for i, v in enumerate(maplayers):
            if hasattr(v, 'ipygis_key'):
                if v.ipygis_key == self.ipygis_key:
                    key_index = 1
                    key_layer = v
                    print('ok', v.name, i)
        self.m.remove_layer(key_layer)
        self.m.add_layer(key_layer)
        self.update_wms_layer(change)
        self.wms_control = self.get_wms_controls()
        # maplayers.insert(key_index-1, maplayers.pop(key_index))
        # self.m.layers = maplayers

    def map_interact_down(self, change):
        maplayers = list(self.m.layers)[::-1]
        for i, v in enumerate(maplayers):
            if hasattr(v, 'ipygis_key'):
                if v.ipygis_key == self.ipygis_key:
                    key_index = 1
                    print('ok', v.name, i)
        maplayers.insert(key_index + 1, maplayers.pop(key_index))
        self.m.layers = maplayers

    def update_wms_visibility(self, change):
        if self.ztwms.visible:
            self.ztwms.visible = False
        else:
            self.ztwms.visible = True

    def update_wms_opacity(self, change):
        self.ztwms.opacity = self.wms_control.children[2].value

    def update_wms_time(self, change):
        self.ztwms.time = "{}".format(self.wms_control.children[4].value)

    def update_wms_elevation(self, change):
        self.ztwms.elevation = "{}".format(
            float(self.wms_control.children[5].value.strip())
        )

    def update_wms_styles(self, change):
        self.ztwms.styles = self.wms_control.children[3].value

    def update_wms_legend(self, change):
        print(
            f"i have been called {self.ztwms.url},  {self.ztwms.layers}, {change.new}, {self.wms}"
        )
        self.wms_control.children[6].value = get_png_legend(
            self.wms.contents[self.ztwms.layers].styles[change.new]["legend"]
        )

    def update_wms_layer(self, change):
        # self.ztwms.name = ET.fromstring(self.wms.getServiceXML().decode()).findall('.//*Layer')[0].findall('.//*Title')[0].text
        # TIME
        print(self.wms_control)
        if self.wms.contents[self.wms_control.children[1].value].timepositions:
            print("has time")
            self.wms_control.children[4].layout.visibility = "visible"
            self.wms_control.children[4].options = self.wms.contents[
                self.wms_control.children[1].value
            ].timepositions
            self.wms_control.children[4].observe(self.update_wms_time, "value")
            self.wms_control.children[6].value = get_png_legend(
                self.wms.contents[self.wms_control.children[1].value].styles[
                    self.wms_control.children[3].value
                ]["legend"]
            )
        else:
            self.wms_control.children[4].layout.visibility = "hidden"
        # ELEVATION
        if self.wms.contents[self.wms_control.children[1].value].elevations:
            print("has Z")
            self.wms_control.children[5].layout.visibility = "visible"
            self.wms_control.children[5].options = self.wms.contents[
                self.wms_control.children[1].value
            ].elevations
            self.wms_control.children[5].observe(self.update_wms_elevation, "value")
        else:
            self.wms_control.children[5].layout.visibility = "hidden"
        # STYLES
        if self.wms.contents[self.wms_control.children[1].value].styles:
            print("has styles")
            self.wms_control.children[3].layout.visibility = "visible"
            self.wms_control.children[3].options = list(
                self.wms.contents[self.wms_control.children[1].value].styles.keys()
            )
            self.wms_control.children[3].observe(self.update_wms_styles, "value")
            self.wms_control.children[3].observe(self.update_wms_legend, "value")
        else:
            self.wms_control.children[3].layout.visibility = "hidden"
        self.ztwms.layers = self.wms_control.children[1].value
        self.wms_control.children[1].layout.visibility = "visible"
