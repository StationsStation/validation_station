//
#[derive(Clone, Debug)]
pub struct Config {
    pub port: u16,
    pub host: String,
    // Extensible configuration schema
    pub proxy_url: String,
}