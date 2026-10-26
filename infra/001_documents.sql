CREATE TABLE IF NOT EXISTS public.documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 200),
  language text NOT NULL CHECK (language IN ('en', 'ko', 'uz')),
  created_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE public.documents IS 'Local learning catalog; no PDF content or user identity stored.';
