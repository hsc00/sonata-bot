{
  lib,
  pkgs,
}:

pkgs.python3Packages.buildPythonApplication {
  pname = "sonata-bot";
  version = "0.1.0";

  src = ./.;

  propagatedBuildInputs = with pkgs.python3Packages; [
    beautifulsoup4
    discordpy
    pandas
    pynacl
    python-dotenv
    peewee
    requests
    rich
    spotipy
  ];

  meta = {
    description = "A Discord bot for music lovers";
    homepage = "https://github.com/hsc00/sonata-bot";
    maintainers = with lib.maintainers; [
      byestorm
      educorreia932
      hsc00
      hypogirl
    ];
  };
}
