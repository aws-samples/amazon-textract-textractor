using System.Collections.Generic;

namespace Amazon.Textract.Model {

	public class Form {
		public List<Field> Fields { get; set; }
		private Dictionary<string, Field> fieldMap;

		public Form() {
			this.Fields = new List<Field>();
			this.fieldMap = new Dictionary<string, Field>();
		}

		public void AddField(Field field) {
			this.Fields.Add(field);
			this.fieldMap.Add(field.Key.ToString(), field);
		}
		public Field GetFieldByKey(string key) {
			return this.fieldMap.GetValueOrDefault(key);
		}

		public List<Field> SearchFieldsByKey(string key) {
			return this.Fields.FindAll(f => f.Key.ToString().ToLower().Contains(key.ToLower()));
		}

		public override string ToString() {
			return string.Join("\n", this.Fields);
		}
	}
}