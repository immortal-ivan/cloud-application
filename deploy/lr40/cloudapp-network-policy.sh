#!/usr/bin/env bash
# Идемпотентное применение сетевой политики Cloud Application (ЛР 40).
# Разрешает доступ к опубликованному порту только с CLIENT_IP, остальное блокирует.
# Политика касается только VM_LAB_IP:PUBLISHED_PORT; SSH, DNS, DHCP и другие службы не затрагиваются.
set -Eeuo pipefail

CONF="${1:-$(dirname "$(readlink -f "$0")")/network-policy.env}"
# shellcheck disable=SC1090
source "$CONF"

CHAIN="CLOUDAPP-LR40"

: "${LAB_IF:?не задан LAB_IF}"
: "${VM_LAB_IP:?не задан VM_LAB_IP}"
: "${PUBLISHED_PORT:?не задан PUBLISHED_PORT}"
: "${CLIENT_IP:?не задан CLIENT_IP}"

# 1. Собственная цепочка (создаётся один раз)
iptables -N "$CHAIN" 2>/dev/null || true

# 2. Пересборка содержимого цепочки
iptables -F "$CHAIN"
iptables -A "$CHAIN" -i "$LAB_IF" -p tcp -d "$VM_LAB_IP" -m conntrack \
  --ctorigdst "$VM_LAB_IP" --ctorigdstport "$PUBLISHED_PORT" -s "$CLIENT_IP" -j ACCEPT
iptables -A "$CHAIN" -i "$LAB_IF" -p tcp -m conntrack \
  --ctorigdst "$VM_LAB_IP" --ctorigdstport "$PUBLISHED_PORT" -j DROP
iptables -A "$CHAIN" -j RETURN

# 3. Ограниченный переход из DOCKER-USER: только для опубликованного порта
JUMP=(-i "$LAB_IF" -p tcp -m conntrack --ctorigdst "$VM_LAB_IP" --ctorigdstport "$PUBLISHED_PORT" -j "$CHAIN")
if ! iptables -C DOCKER-USER "${JUMP[@]}" 2>/dev/null; then
  iptables -I DOCKER-USER 1 "${JUMP[@]}"
fi

echo "CLOUDAPP-LR40 applied: ${VM_LAB_IP}:${PUBLISHED_PORT} allowed from ${CLIENT_IP} only"
