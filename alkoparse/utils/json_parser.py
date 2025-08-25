import time


class JsonParser:
    def __init__(self, raw, og_url):
        self.raw = raw or {}
        self.og_url = og_url or ""

    def parse(self):
        title_base = (self.raw.get("name") or '').strip()
        color = self._get_color()
        volume = self._get_volume()

        title = title_base
        if title_base:
            low = title_base.lower()
            if volume and volume.lower() not in low:
                title = f"{title}, {volume}"
            if color and color.lower() not in low:
                title = f"{title}, {color}"

        price_current, price_original, sale_tag = self._get_prices()

        item = {
            "timestamp": int(time.time()),
            "RPC": self.raw.get("vendor_code") or '',
            "url": self.og_url,
            "title": title or "",
            "marketing_tags": self._get_marketing_tags(),
            "brand": self._get_brand(),
            "section": self._get_section(),
            "price_data": {
                "current": float(price_current or 0.0),
                "original": float(price_original or 0.0),
                "sale_tag": sale_tag,
            },
            "stock": self._get_stock(),
            "assets": self._get_assets(),
            "metadata": self._get_metadata(),
            "variants": 1,
        }

        # if not isinstance(item["marketing_tags"], list):
        #     item["marketing_tags"] = []
        # if not isinstance(item["section"], list):
        #     item["section"] = []
        # for k in ["set_images", "view360", "video"]:
        #     if not isinstance(item["assets"].get(k), list):
        #         item["assets"][k] = []

        return item

    def _blocks(self):
        arr = self.raw.get("description_blocks")
        return arr if isinstance(arr, list) else []

    def _text_blocks(self):
        arr = self.raw.get("text_blocks")
        return arr if isinstance(arr, list) else []

    def _get_color(self):
        for b in self._blocks():
            code = (b.get("code") or "").lower()
            if code == 'cvet':
                vals = b.get("values") or []
                if vals:
                    v = vals[0].get("name") or ''
                    if v:
                        return v
        return ""

    def _get_volume(self):
        for b in self._blocks():
            code = (b.get("code") or "").lower()
            if code == 'obem':
                minimum = b.get("min")
                unit = b.get("unit") or ""
                if minimum is not None:
                    return f"{minimum}{unit}"
        return ""

    def _get_marketing_tags(self):
        tags = []
        allowed = {"dopolnitelno", "tovary-so-skidkoi"}
        arr = self.raw.get("filter_labels") or []
        for i in arr:
            filt = i.get('filter')
            if filt in allowed:
                tags.append(i.get('title'))
        return tags

    def _get_brand(self):
        for blk in self._blocks():
            if (blk.get("code") or "").lower() == 'brend':
                vals = blk.get("values") or []
                if vals:
                    v = vals[0].get("name")
                    if v:
                        return v
        return ""

    def _get_section(self):
        cat = self.raw.get("category") or {}
        names = []
        cur = cat
        safe_guard = 0
        while isinstance(cur, dict) and safe_guard < 10:
            nm = (cur.get("name") or "").strip()
            if nm:
                names.append(nm)
            cur = cur.get("parent")
            safe_guard += 1
        names.reverse()
        return names

    def _get_prices(self):
        cur_raw = self.raw.get("price")
        prev_raw = self.raw.get("prev_price")

        current = float(cur_raw or 0)
        original = float(prev_raw) if prev_raw else current

        sale_tag = ""
        if original > 0 and current < original:
            discount = int(round((original - current) * 100.0 / original))
            sale_tag = f"Скидка {discount}%"
        return current, original, sale_tag

    def _get_stock(self):
        available = self.raw.get('available')
        count = self.raw.get('quantity_total')
        try:
            count = int(count) if count is not None else 0
        except Exception:
            count = 0
        return {"in_stock": available, "count": count}

    def _get_assets(self):
        images = []
        main_photo = self.raw.get('image_url') or ''
        images.append(main_photo)

        return {
            "main_image": main_photo,
            "set_images": images,
            "view360": [],
            "video": [],
        }

    def _get_description(self):
        tb = self._text_blocks()
        if tb:
            first = tb[0]
            val = first.get("content")
            if val:
                return str(val).strip()
        return ''

    def _get_metadata(self):
        data = {"__description": self._get_description()}
        for b in self._blocks():
            title = (b.get("title") or "").strip()
            if not title:
                continue
            unit = (b.get("unit") or "").strip()
            value = ""
            vals = b.get("values")
            if vals:
                v = vals[0]
                v = v.get("name") or ''
                value = v.strip()
            else:
                if b.get("min") is not None and b.get("max") is not None and b.get("min") != b.get("max"):
                    value = f"{b.get('min')}–{b.get('max')}"
                elif b.get("min") is not None:
                    value = str(b.get("min"))
            if unit and value and not value.endswith(unit):
                value = f"{value}{unit}"
            value = value.strip()
            if value:
                data[title] = value

        if self.raw.get("vendor_code") is not None:
            data["Артикул"] = self.raw.get("vendor_code")
        if self.raw.get("uuid"):
            data["Код товара"] = self.raw.get("uuid")
        return data

    def _collect_values_by_code(self, keys):
        out = set()
        keys = [k.lower() for k in keys]
        for b in self._blocks():
            code = (b.get("code") or "").lower()
            title = (b.get("title") or "").lower()
            if code in keys or any(k in title for k in keys):
                vals = b.get("values") or []
                for v in vals:
                    vv = v.get("name") if isinstance(v, dict) else v
                    vv = (str(vv or "")).strip()
                    if vv:
                        out.add(vv)
        return list(out)