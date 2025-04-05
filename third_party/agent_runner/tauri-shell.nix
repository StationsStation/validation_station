let
  pkgs = import <nixpkgs> { };
in
pkgs.mkShell {
  packages = with pkgs; [
    nodejs
    corepack
    # Add AppImage dependencies
    xdg-utils
    fuse
    appimage-run
    appimagekit

    # rust tools
    typeshare
  ];
  nativeBuildInputs =
    with pkgs;
    [
      # Rust toolchain
      rustc
      cargo
      pkg-config
    ]
    # Brings in most of our GTK stuff for Linux
    ++ lib.optionals stdenv.hostPlatform.isLinux [ wrapGAppsHook4 ];
  buildInputs =
    with pkgs;
    [ 
      openssl
      # Add these dependencies for bundling
      xdg-utils  # Make sure it's here too for visibility
    ]
    ++ lib.optionals stdenv.hostPlatform.isLinux [
      # Required for most applications
      glib-networking
      webkitgtk_4_1
      # AppImage dependencies
      squashfsTools
    ]
    ++ lib.optionals stdenv.hostPlatform.isDarwin [
      darwin.apple_sdk.frameworks.WebKit
    ];
  
  # Add this shellHook to ensure XDG-related environment variables are set
  shellHook = ''
    export XDG_DATA_DIRS=${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:$XDG_DATA_DIRS
  '';
}
# let
#   pkgs = import <nixpkgs> { };
#   libraries = with pkgs; [
#     webkitgtk
#     gtk3
#     cairo
#     gdk-pixbuf
#     glib
#     dbus
#     openssl
#     librsvg
#     # X11-specific libraries
#     xorg.libX11
#     xorg.libxcb
#     xorg.libXcomposite
#     xorg.libXcursor
#     xorg.libXdamage
#     xorg.libXext
#     xorg.libXfixes
#     xorg.libXi
#     xorg.libXrandr
#     xorg.libXrender
#     xorg.libXtst
#     # EGL
#     libGL
#     libglvnd
#   ];
#   packages = libraries ++ (with pkgs; [
#     pkg-config
#     dbus
#     glib
#     gtk3
#     libsoup
#     xdg-utils
#     appimagekit
#     rustup
#     cargo-tauri
#   ]);
# in
# pkgs.mkShell {
#   buildInputs = packages;
#   shellHook = ''
#     export PKG_CONFIG_PATH="${pkgs.openssl.dev}/lib/pkgconfig:$PKG_CONFIG_PATH"
#     export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath libraries}:$LD_LIBRARY_PATH
#     export XDG_DATA_DIRS=${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:$XDG_DATA_DIRS
    
#     # X11-specific settings
#     export GDK_BACKEND=x11
#     export WEBKIT_DISABLE_COMPOSITING_MODE=1
#     export LIBGL_ALWAYS_SOFTWARE=1
#   '';
# }