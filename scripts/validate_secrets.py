"""
Validação e gerenciamento de secrets para produção.

Este script valida que todas as secrets necessárias estão configuradas
e fornece utilidades para rotação segura.
"""
import os
import sys
import secrets
import hashlib
from datetime import datetime


class SecretsValidator:
    """Validador de configuração de secrets."""

    REQUIRED_SECRETS = {
        "LLMS_API_KEY": {
            "min_length": 32,
            "description": "API key para autenticação"
        },
        "REDIS_URL": {
            "min_length": 10,
            "description": "URL de conexão Redis"
        }
    }

    OPTIONAL_SECRETS = {
        "CORS_ORIGINS": "Origens CORS permitidas",
        "DATABASE_URL": "URL do banco de dados (futuro)",
        "SENTRY_DSN": "Sentry para error tracking (futuro)",
    }

    @staticmethod
    def generate_api_key(length: int = 64) -> str:
        """Gera uma API key segura."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Valida formato da API key."""
        if not api_key or len(api_key) < 32:
            return False
        # Deve conter caracteres variados
        return any(c.isdigit() for c in api_key) and any(c.isalpha() for c in api_key)

    def check_environment(self, env: str = "production") -> dict:
        """
        Verifica se todas as secrets necessárias estão configuradas.

        Args:
            env: Ambiente (development, staging, production)

        Returns:
            dict: Resultado da validação
        """
        results = {
            "environment": env,
            "timestamp": datetime.now().isoformat(),
            "valid": True,
            "issues": [],
            "warnings": []
        }

        # Em desenvolvimento, secrets são opcionais
        if env == "development":
            results["warnings"].append("Ambiente de desenvolvimento - secrets não são obrigatórias")
            return results

        # Verificar secrets obrigatórias
        for secret_name, config in self.REQUIRED_SECRETS.items():
            value = os.getenv(secret_name)

            if not value:
                results["valid"] = False
                results["issues"].append(f"❌ {secret_name} não configurada - {config['description']}")
            elif len(value) < config["min_length"]:
                results["valid"] = False
                results["issues"].append(
                    f"❌ {secret_name} muito curta (mínimo {config['min_length']} caracteres)"
                )
            else:
                # Secret configurada corretamente
                masked = value[:4] + "****" + value[-4:] if len(value) > 8 else "****"
                results["warnings"].append(f"✅ {secret_name}: {masked}")

        # Verificar secrets opcionais
        for secret_name, description in self.OPTIONAL_SECRETS.items():
            value = os.getenv(secret_name)
            if not value:
                results["warnings"].append(f"⚠️  {secret_name} não configurada (opcional) - {description}")

        # Validação específica da API key
        api_key = os.getenv("LLMS_API_KEY")
        if api_key and not self.validate_api_key(api_key):
            results["valid"] = False
            results["issues"].append("❌ LLMS_API_KEY tem formato inválido (muito simples)")

        return results

    def get_secret_hash(self, secret_name: str) -> str:
        """
        Retorna hash SHA256 de uma secret (para auditoria).

        Útil para verificar se secret mudou sem expor o valor.
        """
        value = os.getenv(secret_name, "")
        return hashlib.sha256(value.encode()).hexdigest()


def main():
    """CLI para validação de secrets."""
    import argparse

    parser = argparse.ArgumentParser(description="Validador de secrets")
    parser.add_argument(
        "--env",
        choices=["development", "staging", "production"],
        default="production",
        help="Ambiente a validar"
    )
    parser.add_argument(
        "--generate-key",
        action="store_true",
        help="Gerar uma nova API key"
    )

    args = parser.parse_args()

    validator = SecretsValidator()

    if args.generate_key:
        print("🔑 Nova API Key gerada:")
        print(f"\n{validator.generate_api_key()}\n")
        print("⚠️  IMPORTANTE: Guarde esta chave em local seguro!")
        print("   - AWS Secrets Manager")
        print("   - HashiCorp Vault")
        print("   - Arquivo .env (apenas dev)")
        return

    # Validar ambiente
    print(f"\n🔒 Validando secrets para: {args.env}\n")
    results = validator.check_environment(args.env)

    # Mostrar warnings
    for warning in results["warnings"]:
        print(warning)

    # Mostrar issues
    if results["issues"]:
        print("\n🚨 PROBLEMAS ENCONTRADOS:\n")
        for issue in results["issues"]:
            print(issue)

    # Resultado final
    print("\n" + "="*50)
    if results["valid"]:
        print("✅ TODAS AS SECRETS ESTÃO CONFIGURADAS CORRETAMENTE")
        sys.exit(0)
    else:
        print("❌ CONFIGURAÇÃO INVÁLIDA - CORRIJA OS PROBLEMAS ACIMA")
        sys.exit(1)


if __name__ == "__main__":
    main()
