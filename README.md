> [!IMPORTANT]
> This application is currently under development. A known issue exists where **a browser opens for every API call**.

# Bear MCP Server
A MCP server for interacting with [Bear](https://bear.app/) note-taking software.

## Installation

### For Goose CLI
To enable the Bear extension in Goose CLI,
edit the configuration file `~/.config/goose/config.yaml` to include the following entry:

```yaml
extensions:
  bear:
    name: Bear
    cmd: uvx
    args: [--from, git+https://github.com/jkawamoto/mcp-bear, mcp-bear]
    envs: { "BEAR_API_TOKEN": "<YOUR_TOKEN>" }
    enabled: true
    type: stdio
```

### For Goose Desktop
Add a new extension with the following settings:

- **Type**: Standard IO
- **ID**: bear
- **Name**: Bear
- **Description**: Interacting with Bear note-taking software
- **Command**: `uvx --from git+https://github.com/jkawamoto/mcp-bear mcp-bear`
- **Environment Variables**: Add `BEAR_API_TOKEN` with your api token

For more details on configuring MCP servers in Goose Desktop,
refer to the documentation:
[Using Extensions - MCP Servers](https://block.github.io/goose/docs/getting-started/using-extensions#mcp-servers).


## Actions Implemented

The server supports the following actions.
Refer to Bear's [X-callback-url Scheme documentation](https://bear.app/faq/x-callback-url-scheme-documentation/) for details on each action.

- [x] /open-note
- [x] /create
- [ ] /add-text
- [ ] /add-file
- [x] /tags
- [x] /open-tag
- [ ] /rename-tag
- [ ] /delete-tag
- [ ] /trash
- [ ] /archive
- [ ] /untagged
- [x] /todo
- [x] /today
- [ ] /locked
- [x] /search
- [x] /grab-url

## License
This application is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
