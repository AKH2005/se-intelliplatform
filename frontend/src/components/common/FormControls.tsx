import React from 'react';

export interface FormFieldProps {
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  htmlFor?: string;
  className?: string;
  children: React.ReactNode;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  hint,
  error,
  required = false,
  htmlFor,
  className = '',
  children,
}) => {
  return (
    <div className={`form-group ${className}`.trim()}>
      {label && (
        <label htmlFor={htmlFor} className="form-label">
          <span>
            {label}
            {required && <span style={{ color: '#ef4444', marginLeft: 4 }}>*</span>}
          </span>
          {hint && !error && <span className="form-hint">{hint}</span>}
        </label>
      )}
      {children}
      {error && <div className="form-error">{error}</div>}
    </div>
  );
};

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  iconPrefix?: React.ReactNode;
  iconSuffix?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  hint,
  error,
  iconPrefix,
  iconSuffix,
  className = '',
  id,
  required,
  ...props
}) => {
  const inputElement = (
    <div className={iconPrefix ? 'input-with-icon' : undefined} style={{ position: 'relative', width: '100%' }}>
      {iconPrefix && <div className="input-icon-prefix">{iconPrefix}</div>}
      <input
        id={id}
        required={required}
        aria-invalid={Boolean(error)}
        className={`form-input ${error ? 'border-danger' : ''} ${className}`.trim()}
        {...props}
      />
      {iconSuffix && (
        <div
          style={{
            position: 'absolute',
            right: '0.75rem',
            top: '50%',
            transform: 'translateY(-50%)',
            display: 'flex',
            alignItems: 'center',
            color: 'var(--text-muted)',
          }}
        >
          {iconSuffix}
        </div>
      )}
    </div>
  );

  if (label || hint || error) {
    return (
      <FormField label={label} hint={hint} error={error} required={required} htmlFor={id}>
        {inputElement}
      </FormField>
    );
  }

  return inputElement;
};

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  hint,
  error,
  className = '',
  id,
  required,
  ...props
}) => {
  const textareaElement = (
    <textarea
      id={id}
      required={required}
      aria-invalid={Boolean(error)}
      className={`form-textarea ${error ? 'border-danger' : ''} ${className}`.trim()}
      {...props}
    />
  );

  if (label || hint || error) {
    return (
      <FormField label={label} hint={hint} error={error} required={required} htmlFor={id}>
        {textareaElement}
      </FormField>
    );
  }

  return textareaElement;
};

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  error?: string;
  options?: { value: string; label: string }[];
}

export const Select: React.FC<SelectProps> = ({
  label,
  hint,
  error,
  options,
  children,
  className = '',
  id,
  required,
  ...props
}) => {
  const selectElement = (
    <select
      id={id}
      required={required}
      aria-invalid={Boolean(error)}
      className={`form-select ${error ? 'border-danger' : ''} ${className}`.trim()}
      {...props}
    >
      {options
        ? options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))
        : children}
    </select>
  );

  if (label || hint || error) {
    return (
      <FormField label={label} hint={hint} error={error} required={required} htmlFor={id}>
        {selectElement}
      </FormField>
    );
  }

  return selectElement;
};

