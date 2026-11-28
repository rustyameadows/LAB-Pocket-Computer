"""Portable 3x5 pixel font for LAB Studio and the Pocket player."""
# Tiny bitmap lettering keeps all three desktop previews and exported frames identical.
GLYPHS = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", [
    "25755","65656","34443","65556","74647","74644","34553","55755","72227",
    "11152","55655","44447","57755","57775","25552","65644","25573","65655",
    "34216","72222","55557","55552","55775","55255","55222","71247",
    "75557","26227","71247","71217","55711","74617","34652","71122","25252","25716",
]))
GLYPHS.update({" ":"00000", "-":"00700", "+":"02720", ".":"00002", ":":"02020",
                "/":"11244", "!":"22202", "?":"61202", "%":"51245", "'":"22000",
                "#":"57575", "<":"12421", ">":"42124", "=":"07070", "_":"00007",
                "[":"62226", "]":"32223", ",":"00024", "(": "12221", ")":"42224",
                "*":"02520", "|":"22222", "×":"05250"})



def draw_text(put_pixel, x, y, value, color, scale=1):
    for char in str(value).upper():
        for dy, row in enumerate(GLYPHS.get(char, GLYPHS["?"])):
            for dx in range(3):
                if int(row) & (4 >> dx):
                    for sy in range(scale):
                        for sx in range(scale):
                            put_pixel(x + dx*scale + sx, y + dy*scale + sy, color)
        x += 4 * scale
