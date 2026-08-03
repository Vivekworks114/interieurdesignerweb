const migrationArticleModules = import.meta.glob('../data/articles/*.json');

export const migratedBlogSlugs = new Set(
  Object.keys(migrationArticleModules).map((path) => path.split('/').pop()!.replace(/\.json$/, '')),
);
