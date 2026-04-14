-- Database schema for IPO Recommendation Agent
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE ipo_cap_size AS ENUM ('Large', 'Mid', 'Small');

CREATE TYPE ipo_status AS ENUM ('cancelled', 'finalized', 'active', 'upcoming');

-- Table: public.ipo

-- DROP TABLE IF EXISTS public.ipo;

CREATE TABLE IF NOT EXISTS public.ipo
(
    ipo_id uuid NOT NULL,
    name character varying(200) COLLATE pg_catalog."default" NOT NULL,
    revenue numeric,
    pe_ratio numeric,
    eps numeric,
    roce numeric,
    roe numeric,
    pat numeric,
    embedding vector(6),
    status ipo_status NOT NULL DEFAULT 'upcoming'::ipo_status,
    cap_size ipo_cap_size NOT NULL,
    ipfs_doc_cid character varying(100) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT ipo_pkey PRIMARY KEY (ipo_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.ipo
    OWNER to postgres;

-- Trigger: trg_create_ipo_vector

-- DROP TRIGGER IF EXISTS trg_create_ipo_vector ON public.ipo;

CREATE OR REPLACE TRIGGER trg_create_ipo_vector
    BEFORE INSERT OR UPDATE 
    ON public.ipo
    FOR EACH ROW
    EXECUTE FUNCTION public.create_ipo_vector();

-- FUNCTION: public.create_ipo_vector()

-- DROP FUNCTION IF EXISTS public.create_ipo_vector();

CREATE OR REPLACE FUNCTION public.create_ipo_vector()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    NEW.embedding = ARRAY[
        NEW.revenue,
        NEW.pe_ratio,
        NEW.eps,
        NEW.roce,
        NEW.roe,
        NEW.pat
    ]::vector;
    RETURN NEW;
END;
$BODY$;

ALTER FUNCTION public.create_ipo_vector()
    OWNER TO postgres;


-- Table: public.transaction

-- DROP TABLE IF EXISTS public.transaction;

CREATE TABLE IF NOT EXISTS public.transaction
(
    transaction_id integer NOT NULL DEFAULT nextval('transaction_transaction_id_seq'::regclass),
    ipo_id uuid NOT NULL,
    wallet_address character varying(255) COLLATE pg_catalog."default" NOT NULL,
    total_amount character varying(100) COLLATE pg_catalog."default",
    transaction_hash character varying(255) COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT transaction_pkey PRIMARY KEY (transaction_id),
    CONSTRAINT transaction_transaction_hash_key UNIQUE (transaction_hash),
    CONSTRAINT fk_transaction_ipo FOREIGN KEY (ipo_id)
        REFERENCES public.ipo (ipo_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.transaction
    OWNER to postgres;