mod broker;
mod provider;
mod shared;
mod constants;

use clap::{Arg, Command};
use crate::shared::Config;


#[actix_web::main]
async fn main() -> anyhow::Result<()> {
    // Parse command-line arguments with semantic validation
    let matches = Command::new("validation_station")
        .version("0.1.0")
        .author("8baller <8baller@station.codes>")
        .about("Distributed validation service with provider/broker architecture")
        .arg(
            Arg::new("broker")
                .long("broker")
                .help("Initialize in broker mode")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("provider")
                .long("provider")
                .help("Initialize in provider mode")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("port")
                .short('P')
                .long("port")
                .help("Port to bind service")
                .value_parser(clap::value_parser!(u16))
                .default_value("8080"),
        )
        .arg(
            Arg::new("host")
                .long("host")
                .help("Host interface to bind")
                .default_value("127.0.0.1"),
        )
        .arg(
            Arg::new("proxy_url")
                .long("proxy_url")
                .help("URL of the proxy server")
                .default_value("http://localhost:8080"),
        )
        .get_matches();

    // Extract configuration parameters
    let config = Config {
        port: *matches.get_one::<u16>("port").unwrap(),
        host: matches.get_one::<String>("host").unwrap().clone(),
        proxy_url: matches.get_one::<String>("proxy_url").unwrap().clone(),
    };

    // Initiate appropriate service based on operational mode selection
    if matches.get_flag("broker") {
        println!("Initializing broker service on {}:{}", config.host, config.port);
        broker::start_service(config).await?;
    } else if matches.get_flag("provider") {
        println!("Initializing provider service on {}:{}", config.host, config.port);
        provider::start_service(config).await?;
    } else {
        println!("Please select either broker or provider mode");
        panic!("Invalid operational mode");
    }

    Ok(())
}