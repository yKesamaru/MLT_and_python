from lxml import etree


def create_mlt_xml_with_oldfilm(input_image, output_xml):
    # MLT XMLのルート要素を作成
    mlt = etree.Element('mlt', version="7.4.0")

    # プロファイルを追加
    profile = etree.SubElement(mlt, 'profile', {
        'description': 'NTSC 720x480 10fps',  # プロファイルの説明
        'width': '720',  # 横幅720px
        'height': '480',  # 縦幅480px
        'progressive': '1',  # プログレッシブスキャン
        'frame_rate_num': '10',  # フレームレートの分子
        'frame_rate_den': '1',  # フレームレートの分母
        'colorspace': '601'  # カラースペース（オプション）
    })

    # プロデューサーを追加
    producer = etree.SubElement(mlt, 'producer', id="producer0")
    property_element = etree.SubElement(producer, 'property', name="resource")
    property_element.text = input_image
    property_element = etree.SubElement(producer, 'property', name="mlt_service")
    property_element.text = 'qimage'

    # プレイリストを追加
    playlist = etree.SubElement(mlt, 'playlist', id="playlist0")
    entry = etree.SubElement(playlist, 'entry', producer="producer0", **{"in": "0", "out": "10"})

    # oldfilmエフェクトを追加
    filter_element = etree.SubElement(playlist, 'filter', id="filter0")
    filter_element.set('mlt_service', 'oldfilm')
    filter_element.set('in', '0')
    filter_element.set('out', '10')
    
    param_delta = etree.SubElement(filter_element, 'property', name="delta")
    param_delta.text = '400'
    param_brightness_up = etree.SubElement(filter_element, 'property', name="brightnessdelta_up")
    param_brightness_up.text = '100'
    param_brightness_down = etree.SubElement(filter_element, 'property', name="brightnessdelta_down")
    param_brightness_down.text = '100'

    # タイムラインを追加
    tractor = etree.SubElement(mlt, 'tractor', id="tractor0")
    track = etree.SubElement(tractor, 'track', producer="playlist0")
    transition = etree.SubElement(tractor, 'transition', {
        'mlt_service': 'mix',
        'in': '0',
        'out': '10'
    })

    # XMLツリーをファイルに保存
    tree = etree.ElementTree(mlt)
    tree.write(output_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8')

if __name__ == "__main__":
    # 使用例
    create_mlt_xml_with_oldfilm("assets/example.png", "output_with_oldfilm.mlt")
