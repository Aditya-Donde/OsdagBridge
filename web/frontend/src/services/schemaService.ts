import { API } from '../store/bridgeStore';

let schemaCache: Record<string, any> | null = null;

export const fetchAllSchemas = async (): Promise<Record<string, any>> => {
  if (schemaCache) {
    return schemaCache;
  }
  try {
    const response = await fetch(`${API}/schemas`);
    if (!response.ok) {
      throw new Error(`Failed to fetch schemas: ${response.statusText}`);
    }
    const data = await response.json();
    schemaCache = data;
    return data;
  } catch (error) {
    console.error('Error fetching schemas:', error);
    throw error;
  }
};

export const getSchema = async (schemaName: string): Promise<any | null> => {
  const schemas = await fetchAllSchemas();
  return schemas[schemaName] || null;
};

export const extractSchemaDefaults = (schemas: Record<string, any>): Record<string, any> => {
  const defaults: Record<string, any> = {};

  const processField = (field: any) => {
    const fieldId = field.id || field.bind;
    if (fieldId && field.default !== undefined) {
      defaults[fieldId] = field.default;
    }
    if (field.type === "mode_line" || field.type === "mode_value") {
      const modeId = field.bind_mode || `${fieldId}_mode`;
      const valId = field.bind_value || fieldId;
      if (field.default_mode) defaults[modeId] = field.default_mode;
      if (field.default_value) defaults[valId] = field.default_value;
    }
    if (field.row_fields) {
      field.row_fields.forEach(processField);
    }
  };

  Object.values(schemas).forEach(schema => {
    if (schema.rows) {
      schema.rows.forEach((row: any) => {
        if (row.fields) row.fields.forEach(processField);
      });
    }
    if (schema.sections) {
      schema.sections.forEach((section: any) => {
        if (section.fields) section.fields.forEach(processField);
        if (section.type === "checkbox_list" && section.bind) {
          const checkedState: Record<string, boolean> = {};
          section.items?.forEach((item: string) => {
            checkedState[item] = section.default_checked ?? false;
          });
          defaults[section.bind] = checkedState;
        }
      });
    }
  });

  return defaults;
};
