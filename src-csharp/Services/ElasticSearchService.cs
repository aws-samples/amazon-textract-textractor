using System;
using Nest;

namespace Dotnet_Core.Services {
	public class ElasticSearchService {
		// private string domainUri, defaultIndex;
		private ElasticClient elasticClient;
		public ElasticSearchService(string endpoint, string domainName) {
			var connectionSettings = new ConnectionSettings(new Uri(endpoint));
			connectionSettings.DefaultIndex(domainName);
			this.elasticClient = new ElasticClient(connectionSettings);
		}

		public void Index<T>(T item, string indexName) where T : class {
			this.elasticClient.Index<T>(item, x => x.Index(indexName));
		}
	}
}