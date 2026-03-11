FROM ubuntu:24.04

ARG CLAUDE_CODE_VERSION=latest
ARG GIT_DELTA_VERSION=0.18.2
ARG EZA_VERSION=0.23.4
ARG TZ=UTC

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=${TZ}

# Base system packages
RUN apt-get update && apt-get install -y \
    curl less git procps sudo fzf zsh bat man-db unzip gnupg2 openssh-client gh jq nano vim wget \
    python3 python3-pip python3-venv make \
    && rm -rf /var/lib/apt/lists/*

# git-delta (multi-arch)
RUN ARCH=$(dpkg --print-architecture) && \
    curl -Lo /tmp/git-delta.deb \
    "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" \
    && dpkg -i /tmp/git-delta.deb && rm /tmp/git-delta.deb

# eza (multi-arch)
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then EZA_ARCH="aarch64-unknown-linux-gnu"; else EZA_ARCH="x86_64-unknown-linux-gnu"; fi && \
    curl -Lo /tmp/eza.tar.gz \
    "https://github.com/eza-community/eza/releases/download/v${EZA_VERSION}/eza_${EZA_ARCH}.tar.gz" \
    && tar -xzf /tmp/eza.tar.gz -C /usr/local/bin && rm /tmp/eza.tar.gz

# starship
RUN curl -fsSL https://starship.rs/install.sh | sh -s -- --yes

# zoxide
RUN curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh

# Node.js 24.x + Claude Code
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# vscode user
RUN useradd -m -s /bin/zsh vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /commandhistory && chown vscode:vscode /commandhistory && \
    mkdir -p /home/vscode/bin

# uv (Python package manager)
USER vscode
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# zshrc
RUN cat > /home/vscode/.zshrc << 'EOF'
export PATH="$HOME/bin:$HOME/.local/bin:/usr/local/share/npm-global/bin:$PATH"

alias ls='eza'
alias ll='eza -la'
alias cat='bat'
alias rm='echo "use /bin/rm explicitly"; false'
alias yoco='claude --dangerously-skip-permissions'

export HISTFILE=/commandhistory/.bash_history
export PROMPT_COMMAND='history -a'

autoload -U up-line-or-beginning-search down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search
bindkey "^[[A" up-line-or-beginning-search
bindkey "^[[B" down-line-or-beginning-search

eval "$(starship init zsh)"
eval "$(fzf --zsh)"
eval "$(zoxide init zsh)"
EOF
