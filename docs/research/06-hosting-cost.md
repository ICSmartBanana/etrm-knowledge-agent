# 6. Hosting cost: Azure Container Apps and alternatives

## Azure Container Apps (Consumption plan)

- **Free grant, per subscription per month:** 180,000 vCPU-seconds, 360,000 GiB-seconds and 2 million requests. Usage beyond that is billed per second.
- **Scale to zero** works only on the Consumption profile and only with `minReplicas = 0`. The trade-off is cold starts. One source reported the slowest cold starts of the big three clouds, but that measurement was for Azure Functions, not Container Apps.
- **Indicative rates** (third-party, June 2026, US East): about $0.000024 per vCPU-second and $0.000003 per GiB-second. Idle minimum replicas are billed at a reduced rate. A single always-on vCPU works out to roughly **$63/month** in compute alone.
- **For our demo:** the API and UI are idle most of the time with light traffic, so they should fit inside the free grant and cost close to $0. **Verify** in the Azure pricing calculator for the chosen region.

## Azure Database for PostgreSQL Flexible Server (this is the real cost)

- Unlike Container Apps, it **doesn't scale to zero**. The smallest tier is **Burstable B1ms** (1 vCore, 2 GiB RAM).
- **Stopping the server** stops compute billing straight away, but storage and backups are still billed. **Azure automatically restarts a stopped server after 7 days**, so a scheduled stop job is needed, not a one-off stop.
- The search didn't return a B1ms monthly price or confirm the pgvector extension (`vector`) is available. **Verify both** in the pricing calculator and the Azure Postgres extensions docs before M6.

## Alternatives

App Service and Fly.io weren't covered by the search results, so there's **no comparison yet**. App Service Standard came up only as about $73/month fixed in one estimator, which is worse than Container Apps for idle workloads. Since the brief already targets Azure because the company is on Azure, a full comparison isn't on the M0 critical path. It's logged as an open item for M6.

## Sources

- [Azure Container Apps pricing (official)](https://azure.microsoft.com/en-us/pricing/details/container-apps/) · [Container Apps billing (docs)](https://docs.azure.cn/en-us/container-apps/billing)
- [DevZero: Azure Container Apps pricing](https://www.devzero.io/blog/azure-container-apps-pricing) · [nOps: Container Apps cost optimisation](https://nops.io/blog/azure-container-apps-cost-optimization-guide) · [CloudToolStack estimator](https://cloudtoolstack.com/tools/azure-container-apps-cost-estimator) · [freetier.co](https://freetier.co/directory/products/azure-container-apps)
- [Azure Postgres Flexible Server pricing (official)](https://azure.microsoft.com/pricing/details/postgresql/) · [Compute and storage options](https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-compute-storage) · [Stop a server](https://learn.microsoft.com/azure/postgresql/configure-maintain/how-to-stop-server) · [Q&A: auto-restart after stop](https://learn.microsoft.com/en-us/answers/questions/2223469/shut-down-azure-postgresql-without-azure-restartin) · [nOps: Postgres cost optimisation](https://www.nops.io/blog/azure-database-postgresql-cost-optimization/)
