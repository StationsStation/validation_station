let
  pkgs = import <nixpkgs> { };

  libraries = with pkgs;[
    webkitgtk
    gtk3
    cairo
    gdk-pixbuf
    glib
    dbus
    openssl_3
    librsvg
    pkg-config
  ];

  packages = with pkgs; [
    pkg-config
    dbus
    openssl_3
    glib
    gtk3
    libsoup
    webkitgtk
    gdk-pixbuf
    webkitgtk_4_1
    webkitgtk_4_1.dev
    appimagekit
    librsvg
  ];
in
pkgs.mkShell {
  buildInputs = packages;

  shellHook =
    ''

      export PKG_CONFIG_PATH = "${pkgs.openssl.dev}/lib/pkgconfig";
      export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath libraries}:$LD_LIBRARY_PATH
      export XDG_DATA_DIRS=${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:$XDG_DATA_DIRS
    '';
}
